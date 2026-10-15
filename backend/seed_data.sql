-- Optional sample data. Run AFTER `alembic upgrade head`:
--   sqlite3 voting.db < seed_data.sql
-- Idempotent: rows are keyed by title, so re-running does not duplicate anything.
-- Timestamps are UTC. Votes are attached to the first registered users (if any exist).

INSERT INTO proposals (title, description, created_at, deadline, status)
SELECT 'Install solar panels on the community hall',
       'Should the community fund rooftop solar panels for the hall to cut electricity costs?',
       datetime('now'), datetime('now', '+2 days'), 'ACTIVE'
WHERE NOT EXISTS (SELECT 1 FROM proposals WHERE title = 'Install solar panels on the community hall');

INSERT INTO proposals (title, description, created_at, deadline, status)
SELECT 'Weekly farmers market in the square',
       'Should we host a weekly farmers market in the central square on Saturdays?',
       datetime('now'), datetime('now', '+5 days'), 'ACTIVE'
WHERE NOT EXISTS (SELECT 1 FROM proposals WHERE title = 'Weekly farmers market in the square');

INSERT INTO proposals (title, description, created_at, deadline, status)
SELECT 'Extend library opening hours (closed example)',
       'Extend library hours to 9pm on weekdays. Manually closed by an admin.',
       datetime('now', '-3 days'), datetime('now', '+4 days'), 'CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM proposals WHERE title = 'Extend library opening hours (closed example)');

INSERT INTO proposals (title, description, created_at, deadline, status)
SELECT 'Street lighting upgrade (expired example)',
       'Replace old street lamps with LED lighting. Deadline already passed.',
       datetime('now', '-6 days'), datetime('now', '-2 days'), 'EXPIRED'
WHERE NOT EXISTS (SELECT 1 FROM proposals WHERE title = 'Street lighting upgrade (expired example)');

-- Sample votes from the earliest users (skipped automatically when users/proposals are missing)
INSERT OR IGNORE INTO votes (proposal_id, user_id, vote, created_at)
SELECT p.id, u.id, 'YES', datetime('now')
FROM proposals p, (SELECT id FROM users WHERE role = 'USER' ORDER BY id LIMIT 1) u
WHERE p.title = 'Install solar panels on the community hall';

INSERT OR IGNORE INTO votes (proposal_id, user_id, vote, created_at)
SELECT p.id, u.id, 'NO', datetime('now')
FROM proposals p, (SELECT id FROM users WHERE role = 'USER' ORDER BY id LIMIT 1 OFFSET 1) u
WHERE p.title = 'Install solar panels on the community hall';
