"""Budget-safe single and exhaustive double transfers using FPL-point forecasts."""
from collections import Counter
from itertools import combinations
from app.database import SessionLocal
from app.models import Player
from app.services.squad_service import validate_squad
from app.services.fpl_forecast_service import build_forecasts


def get_recommendation_strength(score_gain):
    return 'strong' if score_gain >= 2 else 'moderate' if score_gain >= 1 else 'slight' if score_gain > 0 else 'none'


def prepare_context(current_gameweek, owned_player_ids, bank_tenths, selling_prices_tenths=None):
    if not 1 <= current_gameweek <= 38 or bank_tenths < 0:
        return {'error': 'Invalid gameweek or bank'}
    validation = validate_squad(owned_player_ids)
    if not validation['valid']:
        return {'error': 'Invalid squad', 'validation': validation}
    selling = selling_prices_tenths or {}
    if not set(selling).issubset(owned_player_ids) or any(type(v) is not int or v < 0 for v in selling.values()):
        return {'error': 'Invalid selling prices'}
    with SessionLocal() as db:
        result = build_forecasts(db, current_gameweek)
    if 'error' in result:
        return result
    missing = sorted(set(owned_player_ids) - result['by_id'].keys())
    if missing:
        return {'error': 'Analysis unavailable for owned players without official FPL history',
                'missing_player_ids': missing, 'data_quality': result['data_quality']}
    owned = [result['by_id'][pid] for pid in owned_player_ids]
    result.update(owned=owned, owned_ids=set(owned_player_ids), bank=bank_tenths,
                  team_counts=Counter(p['team_id'] for p in owned),
                  selling={p['player_id']: selling.get(p['player_id'], p['price_tenths']) for p in owned})
    if any(v is None for v in result['selling'].values()):
        return {'error': 'Missing selling price for an owned player'}
    assumed = sorted(set(owned_player_ids) - set(selling))
    result['selling_price_assumptions'] = assumed
    if assumed:
        result['warnings'].append('Selling prices were not supplied for every owned player; current market prices are assumed. Enter actual selling values before acting.')
    return result


def public_player(record):
    return {**{k: record[k] for k in ('player_id', 'name', 'team_id', 'team_name', 'position', 'price_tenths')},
            'score': round(record['overall_score'], 2)}


def make_move(outgoing, incoming, multiplier=1):
    return {'player_out': public_player(outgoing), 'player_in': public_player(incoming),
            'score_gain': round((incoming['overall_score'] - outgoing['overall_score']) * multiplier, 2)}


def candidates(context, outgoing):
    return [p for p in context['rankings'].get(outgoing['position'], [])
            if p['player_id'] not in context['owned_ids'] and p['can_buy']]


def legal_clubs(context, outs, ins):
    counts = context['team_counts'].copy()
    counts.subtract(p['team_id'] for p in outs)
    counts.update(p['team_id'] for p in ins)
    return max(counts.values(), default=0) <= 3


def single_options(context):
    result = []
    for outgoing in context['owned']:
        budget = context['selling'][outgoing['player_id']] + context['bank']
        for incoming in candidates(context, outgoing):
            multiplier = context.get('multipliers', {}).get(outgoing['player_id'], 1)
            gain = (incoming['overall_score'] - outgoing['overall_score']) * multiplier
            if gain <= 0 or incoming['price_tenths'] > budget or not legal_clubs(context, [outgoing], [incoming]):
                continue
            move = make_move(outgoing, incoming, multiplier)
            move.update(recommendation_strength=get_recommendation_strength(gain),
                        available_budget_tenths=budget, remaining_bank_tenths=budget - incoming['price_tenths'])
            result.append(move)
    return sorted(result, key=lambda m: (-m['score_gain'], m['player_in']['player_id'], m['player_out']['player_id']))


def double_options(context):
    """Exact best five feasible pairs. No score-only candidate truncation."""
    best = []
    seen = set()
    for out1, out2 in combinations(context['owned'], 2):
        budget = context['selling'][out1['player_id']] + context['selling'][out2['player_id']] + context['bank']
        weight1 = context.get('multipliers', {}).get(out1['player_id'], 1)
        weight2 = context.get('multipliers', {}).get(out2['player_id'], 1)
        if weight1 == weight2 == 0:
            continue
        first = [p for p in candidates(context, out1) if p['price_tenths'] <= budget]
        second = [p for p in candidates(context, out2) if p['price_tenths'] <= budget]
        # Rankings descend by score, enabling safe bounds without losing cheap enablers.
        for in1 in first:
            for in2 in second:
                gain = round((in1['overall_score'] - out1['overall_score']) * weight1 + (in2['overall_score'] - out2['overall_score']) * weight2, 2)
                if gain <= 0 or (len(best) == 5 and gain < best[-1]['combined_score_gain']):
                    break
                cost = in1['price_tenths'] + in2['price_tenths']
                if in1['player_id'] == in2['player_id'] or cost > budget:
                    continue
                if not legal_clubs(context, [out1, out2], [in1, in2]):
                    continue
                key = (tuple(sorted([out1['player_id'], out2['player_id']])),
                       tuple(sorted([in1['player_id'], in2['player_id']])))
                if 'multipliers' in context:
                    key = (out1['player_id'], in1['player_id'], out2['player_id'], in2['player_id'])
                if key in seen:
                    continue
                seen.add(key)
                best.append({'transfers': [make_move(out1, in1, weight1), make_move(out2, in2, weight2)],
                             'combined_score_gain': gain, 'remaining_bank_tenths': budget - cost})
                best.sort(key=lambda p: -p['combined_score_gain'])
                del best[5:]
    return best


def metadata(context):
    return {k: context[k] for k in ('model', 'score_units', 'horizon_gameweeks', 'lookback_gameweeks',
                                   'warnings', 'data_quality', 'selling_price_assumptions')}


def get_transfer_candidates(current_player_id, current_gameweek, owned_player_ids, bank_tenths=0, limit=5, selling_prices_tenths=None):
    context = prepare_context(current_gameweek, owned_player_ids, bank_tenths, selling_prices_tenths)
    if 'error' in context:
        return context
    if current_player_id not in context['owned_ids']:
        return {'error': 'Current player is not in the owned squad'}
    moves = [m for m in single_options(context) if m['player_out']['player_id'] == current_player_id]
    outgoing = context['by_id'][current_player_id]
    options = [{**m['player_in'], 'overall_score': m['player_in']['score'],
                'score_gain': m['score_gain'], 'recommendation_strength': m['recommendation_strength']} for m in moves[:limit]]
    return {**metadata(context), 'current_player_id': current_player_id,
            'current_player_score': outgoing['overall_score'], 'current_player_price_tenths': outgoing['price_tenths'],
            'bank_tenths': bank_tenths, 'available_budget_tenths': context['selling'][current_player_id] + bank_tenths,
            'position': outgoing['position'], 'upgrade_found': bool(options), 'candidates': options}


def get_best_squad_transfer(current_gameweek, owned_player_ids, bank_tenths=0, selling_prices_tenths=None):
    context = prepare_context(current_gameweek, owned_player_ids, bank_tenths, selling_prices_tenths)
    if 'error' in context:
        return context
    options = single_options(context)
    unique = []
    seen = set()
    for option in options:
        incoming = option['player_in']['player_id']
        if incoming not in seen:
            unique.append(option)
            seen.add(incoming)
        if len(unique) == 5:
            break
    return {**metadata(context), 'upgrade_found': bool(unique), 'best_transfer': unique[0] if unique else None,
            'alternatives': unique[1:], 'skipped_players': []}


def get_best_double_transfer(current_gameweek, owned_player_ids, bank_tenths=0, candidates_per_player=10, selling_prices_tenths=None):
    context = prepare_context(current_gameweek, owned_player_ids, bank_tenths, selling_prices_tenths)
    if 'error' in context:
        return context
    options = double_options(context)
    return {**metadata(context), 'search': 'exhaustive_feasible_pairs', 'upgrade_found': bool(options),
            'best_transfer_pair': options[0] if options else None, 'alternatives': options[1:]}


def build_strategy_reason(recommended_strategy, single_transfer, double_transfer):
    single = single_transfer['net_score_gain'] if single_transfer else 0
    double = double_transfer['net_score_gain'] if double_transfer else 0
    moves = []
    if recommended_strategy == 'single_transfer':
        moves = [single_transfer['transfer']]
    elif recommended_strategy == 'double_transfer':
        moves = double_transfer['transfer_pair']['transfers']
    return {'summary': 'Keep the squad; no feasible move improves expected points after hits.' if not moves else
            'This option provides the highest estimated FPL-point gain after transfer hits.',
            'decision_detail': f'Single: {single:.2f}; double: {double:.2f} expected net FPL points over the forecast horizon. Keeping the squad gains 0.',
            'recommended_moves': [{'player_out': m['player_out']['name'], 'player_in': m['player_in']['name']} for m in moves],
            'single_raw_gain': single_transfer['raw_score_gain'] if single_transfer else None,
            'single_net_gain': single, 'double_raw_gain': double_transfer['raw_score_gain'] if double_transfer else None,
            'double_transfer_cost': double_transfer['transfer_cost'] if double_transfer else 0, 'double_net_gain': double}


def get_transfer_strategy(current_gameweek, owned_player_ids, bank_tenths=0, free_transfers=1, candidates_per_player=10, selling_prices_tenths=None, starting_player_ids=None, bench_player_ids=None, captain_id=None, vice_captain_id=None):
    if not 0 <= free_transfers <= 5:
        return {'error': 'Free transfers must be 0–5'}
    context = prepare_context(current_gameweek, owned_player_ids, bank_tenths, selling_prices_tenths)
    if 'error' in context:
        return context
    if context['horizon_gameweeks'] == 0:
        return {'error': 'There are no future gameweeks in this season to forecast'}
    validation = configure_lineup(context, starting_player_ids, bench_player_ids, captain_id, vice_captain_id)
    if validation:
        return validation
    singles, doubles = single_options(context), double_options(context)
    single = double = None
    if singles:
        cost = max(1 - free_transfers, 0) * 4
        single = {'transfer': singles[0], 'raw_score_gain': singles[0]['score_gain'],
                  'transfer_cost': cost, 'net_score_gain': round(singles[0]['score_gain'] - cost, 2)}
    if doubles:
        cost = max(2 - free_transfers, 0) * 4
        double = {'transfer_pair': doubles[0], 'raw_score_gain': doubles[0]['combined_score_gain'],
                  'transfer_cost': cost, 'net_score_gain': round(doubles[0]['combined_score_gain'] - cost, 2)}
    choices = [('no_transfer', 0), ('single_transfer', single['net_score_gain'] if single else 0),
               ('double_transfer', double['net_score_gain'] if double else 0)]
    strategy, gain = max(choices, key=lambda item: item[1])
    baseline = lineup_breakdown(context, [], 0)
    if single:
        single['projection'] = lineup_breakdown(context, [single['transfer']], single['transfer_cost'])
    if double:
        double['projection'] = lineup_breakdown(context, double['transfer_pair']['transfers'], double['transfer_cost'])
    return {**metadata(context), 'baseline': baseline, 'lineup_mode': 'fixed_starting_xi', 'recommended_strategy': strategy, 'best_net_score_gain': gain,
            'free_transfers': free_transfers, 'single_transfer': single, 'double_transfer': double,
            'reason': build_strategy_reason(strategy, single, double)}


def configure_lineup(context, starters, bench, captain, vice):
    if not isinstance(starters, list) or not isinstance(bench, list) or len(starters) != 11 or len(bench) != 4:
        return {'error': 'Choose a starting XI and four substitutes on My Squad before analysis'}
    ids = starters + bench
    if len(set(ids)) != 15 or set(ids) != context['owned_ids']:
        return {'error': 'Starting XI and bench must contain every owned player exactly once'}
    if captain == vice or captain not in starters or vice not in starters:
        return {'error': 'Choose different captain and vice-captain from the starting XI'}
    positions = Counter(context['by_id'][pid]['position'] for pid in starters)
    if positions['Goalkeeper'] != 1 or not 3 <= positions['Defender'] <= 5 or not 2 <= positions['Midfielder'] <= 5 or not 1 <= positions['Attacker'] <= 3:
        return {'error': 'Invalid starting formation: choose one goalkeeper, at least three defenders, two midfielders and one forward'}
    if context['by_id'][bench[0]]['position'] != 'Goalkeeper':
        return {'error': 'The first bench slot must be the reserve goalkeeper'}
    context['multipliers'] = {pid: (2 if pid == captain else 1 if pid in starters else 0) for pid in ids}
    context['starters'] = starters
    context['captain'] = captain
    context['vice_captain'] = vice
    context['warnings'] = [warning for warning in context['warnings'] if not warning.startswith('Gains assume')]
    context['warnings'] += [
        'Forecast uses your fixed starting XI. Incoming players inherit the outgoing player’s starting or bench slot and captaincy; lineups are not re-optimized.',
        'Bench points, automatic substitutions and vice-captain fallback are excluded. Captain points count twice; chips are not modeled.'
    ]
    return None


def lineup_breakdown(context, moves, hit):
    replacements = {move['player_out']['player_id']: move['player_in']['player_id'] for move in moves}
    rows = []
    # The same selected XI and captain apply to every week; hits are charged once.
    weeks = sorted({week for record in context['by_id'].values() for week in record.get('gameweek_points', {})})
    for index, week in enumerate(weeks):
        before = after = 0.0
        for pid in context['starters']:
            multiplier = context['multipliers'][pid]
            before += context['by_id'][pid]['gameweek_points'].get(week, 0) * multiplier
            after += context['by_id'][replacements.get(pid, pid)]['gameweek_points'].get(week, 0) * multiplier
        raw = after - before
        cost = hit if index == 0 else 0
        rows.append({'gameweek': week, 'before_points': round(before, 4), 'after_points': round(after, 4),
                     'raw_gain': round(raw, 4), 'transfer_hit': cost, 'net_gain': round(raw - cost, 4)})
    return {'gameweeks': rows, 'before_points': round(sum(row['before_points'] for row in rows), 2),
            'after_points': round(sum(row['after_points'] for row in rows), 2),
            'transfer_hit': hit, 'net_gain': round(sum(row['raw_gain'] for row in rows) - hit, 2)}
