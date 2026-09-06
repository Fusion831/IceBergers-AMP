-- Enable PostGIS extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'AMIP PostGIS extensions successfully initialized';
END $$;
