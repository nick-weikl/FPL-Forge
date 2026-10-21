# FPL Forge frontend

React and TypeScript interface for squad selection, fixture planning, and transfer analysis.

See the [repository README](../README.md) for setup and [deployment guide](../DEPLOYMENT.md) for production configuration.

## Development checks

- `npm run dev`: start the development server.
- `npm test`: run the frontend unit tests.
- `npm run lint`: check React and TypeScript code.
- `npm run build`: type-check and build production assets.
- `npm run format`: format frontend source and repository documentation/configuration.
- `npm run format:check`: verify formatting without changing files.

The frontend stores squads and preferences in browser storage. Never put secrets in `VITE_` variables; their values are included in the public build.
