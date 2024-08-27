-- Your SQL goes here
CREATE TABLE IF NOT EXISTS INGESTION_USAGE (
    task_id TEXT PRIMARY KEY,
    user_id TEXT,
    api_key TEXT,
    usage_type TEXT,
    usage FLOAT,
    usage_unit TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS USAGE_LIMIT (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    usage_type TEXT,
    usage_limit FLOAT,
    usage_unit TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS INGESTION_TASKS (
    task_id TEXT PRIMARY KEY,
    file_count INTEGER,
    total_size BIGINT,
    total_pages INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
    finished_at TEXT,
    api_key TEXT,
    status TEXT,
    url TEXT,
    model TEXT,
    expiration_time TIMESTAMP WITH TIME ZONE,
    message TEXT,
    FOREIGN KEY (api_key) REFERENCES api_keys(key) ON DELETE CASCADE
);

-- Create INGESTION_FILES table
CREATE TABLE IF NOT EXISTS INGESTION_FILES (
    id Text,
    file_id TEXT PRIMARY KEY,
    task_id TEXT,
    file_name TEXT,
    file_size BIGINT,
    page_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
    status TEXT,
    input_location TEXT,
    output_location TEXT,
    expiration_time TIMESTAMP WITH TIME ZONE,
    model TEXT,
    FOREIGN KEY (task_id) REFERENCES INGESTION_TASKS(task_id) ON DELETE CASCADE
);

CREATE OR REPLACE FUNCTION update_api_key_usage() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.api_key_usage (api_key, usage, usage_type, service)
    VALUES (NEW.api_key, NEW.total_pages, 'page_count', 'ingestion')
    ON CONFLICT (api_key, usage_type, service)
    DO UPDATE SET usage = public.api_key_usage.usage + NEW.total_pages;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update API key usage after inserting a new ingestion task
CREATE TRIGGER update_api_key_usage_trigger
AFTER INSERT ON INGESTION_TASKS
FOR EACH ROW
EXECUTE FUNCTION update_api_key_usage();