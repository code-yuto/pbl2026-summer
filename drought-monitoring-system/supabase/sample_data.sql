INSERT INTO public.monitoring_data (
    device_id,
    soil_moisture,
    water_level,
    risk_level
)
VALUES
    ('SIMULATED_01', 52, 18, 'normal'),
    ('SIMULATED_01', 34, 11, 'medium'),
    ('SIMULATED_01', 23, 7, 'high'),
    ('SIMULATED_01', 18, 4, 'critical');
