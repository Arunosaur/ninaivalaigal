-- Create a test user for graph intelligence testing
INSERT INTO users (
    id,
    email,
    password_hash,
    name,
    is_verified,
    created_at,
    updated_at
) VALUES (
    1,
    'test@ninaivalaigal.com',
    '$2b$12$LQv3c1yqBwEHxPuNYuTuT.BVf1ejmflPDcwLcaekRWC/vUiKvRg/2', -- 'testpassword123'
    'Test User',
    true,
    NOW(),
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    name = EXCLUDED.name,
    is_verified = EXCLUDED.is_verified,
    updated_at = NOW();
