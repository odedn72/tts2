// TDD: MSW server setup
// Written from spec 13

import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
