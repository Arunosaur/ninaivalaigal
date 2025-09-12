-- PostgreSQL schema update for cross-team approval workflow
-- Run this to update your PostgreSQL database with cross-team approval functionality

CREATE TABLE IF NOT EXISTS cross_team_approval_requests (
    id SERIAL PRIMARY KEY,
    context_id INTEGER NOT NULL,
    requesting_team_id INTEGER NOT NULL,
    target_team_id INTEGER NOT NULL,
    requested_by INTEGER NOT NULL,
    permission_level VARCHAR(50) NOT NULL,
    justification TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approved_by INTEGER,
    approved_at TIMESTAMP,
    rejected_by INTEGER,
    rejected_at TIMESTAMP,
    rejection_reason TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (context_id) REFERENCES contexts (id),
    FOREIGN KEY (requesting_team_id) REFERENCES teams (id),
    FOREIGN KEY (target_team_id) REFERENCES teams (id),
    FOREIGN KEY (requested_by) REFERENCES users (id),
    FOREIGN KEY (approved_by) REFERENCES users (id),
    FOREIGN KEY (rejected_by) REFERENCES users (id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON cross_team_approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_target_team ON cross_team_approval_requests(target_team_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_expires ON cross_team_approval_requests(expires_at);

-- Add relationship columns to contexts table if not already present
-- ALTER TABLE contexts ADD COLUMN IF NOT EXISTS team_id INTEGER REFERENCES teams(id);
-- ALTER TABLE contexts ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id);
