export interface Player {
    id: number;
    external_api_id: number; 
    team_id: number;
    team_name: string | null;
    name: string;
    position: string;
    price_tenths: number
}