-- Preserve the exact ESP32 USB Serial payload alongside calibrated values.
-- The existing soil_moisture and water_level columns remain percentages used
-- by risk calculations and dashboard charts.

ALTER TABLE public.monitoring_data
    ADD COLUMN IF NOT EXISTS message_type TEXT NOT NULL DEFAULT 'data',
    ADD COLUMN IF NOT EXISTS sensor_transport TEXT NOT NULL DEFAULT 'http',
    ADD COLUMN IF NOT EXISTS soil_moisture_raw INTEGER,
    ADD COLUMN IF NOT EXISTS water_level_raw INTEGER,
    ADD COLUMN IF NOT EXISTS device_timestamp_ms BIGINT,
    ADD COLUMN IF NOT EXISTS raw_payload JSONB;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'monitoring_data_message_type_check'
    ) THEN
        ALTER TABLE public.monitoring_data
            ADD CONSTRAINT monitoring_data_message_type_check
            CHECK (message_type IN ('data', 'alert'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'monitoring_data_sensor_transport_check'
    ) THEN
        ALTER TABLE public.monitoring_data
            ADD CONSTRAINT monitoring_data_sensor_transport_check
            CHECK (sensor_transport IN ('http', 'usb_serial'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'monitoring_data_soil_raw_check'
    ) THEN
        ALTER TABLE public.monitoring_data
            ADD CONSTRAINT monitoring_data_soil_raw_check
            CHECK (
                soil_moisture_raw IS NULL
                OR soil_moisture_raw BETWEEN 0 AND 4095
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'monitoring_data_water_raw_check'
    ) THEN
        ALTER TABLE public.monitoring_data
            ADD CONSTRAINT monitoring_data_water_raw_check
            CHECK (
                water_level_raw IS NULL
                OR water_level_raw BETWEEN 0 AND 4095
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'monitoring_data_timestamp_ms_check'
    ) THEN
        ALTER TABLE public.monitoring_data
            ADD CONSTRAINT monitoring_data_timestamp_ms_check
            CHECK (
                device_timestamp_ms IS NULL
                OR device_timestamp_ms >= 0
            );
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS monitoring_data_message_type_idx
    ON public.monitoring_data (message_type, created_at DESC);

CREATE INDEX IF NOT EXISTS monitoring_data_device_uptime_idx
    ON public.monitoring_data (device_id, device_timestamp_ms DESC);

COMMENT ON COLUMN public.monitoring_data.message_type IS
    'Value of the ESP32 JSON type field: data or alert.';
COMMENT ON COLUMN public.monitoring_data.soil_moisture_raw IS
    'Original ESP32 ADC soil-moisture value from 0 to 4095.';
COMMENT ON COLUMN public.monitoring_data.water_level_raw IS
    'Original ESP32 ADC water-level value from 0 to 4095.';
COMMENT ON COLUMN public.monitoring_data.device_timestamp_ms IS
    'ESP32 uptime in milliseconds; this is not a calendar timestamp.';
COMMENT ON COLUMN public.monitoring_data.raw_payload IS
    'Unmodified JSON object received from the ESP32.';
