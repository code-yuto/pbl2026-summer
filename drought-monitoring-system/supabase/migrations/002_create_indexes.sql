CREATE INDEX IF NOT EXISTS monitoring_data_created_at_idx
    ON public.monitoring_data (created_at DESC);

CREATE INDEX IF NOT EXISTS monitoring_data_device_created_at_idx
    ON public.monitoring_data (device_id, created_at DESC);

CREATE INDEX IF NOT EXISTS monitoring_data_risk_level_idx
    ON public.monitoring_data (risk_level);
