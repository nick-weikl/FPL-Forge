"""Retired destructive entry point: preserve saved squad IDs and observations."""


def rebuild_fpl_data(apply=False):
    raise RuntimeError(
        'Destructive rebuild is retired. Run app.scripts.migrate, then '
        'app.scripts.download_fpl_dump and app.scripts.import_fpl_dump. '
        'The archive importer preserves existing IDs and match history.'
    )


if __name__ == '__main__':
    raise SystemExit(str(rebuild_fpl_data()))
