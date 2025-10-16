-- CREATE
INSERT INTO users (email, name, pwd_hash, role)
VALUES (:email, :name, :pwd_hash, COALESCE(:role, 'user'))
RETURNING id, email, name, role, created_at;

-- READ
SELECT id, email, name, role, created_at FROM users WHERE id = :id;
SELECT id, email, pwd_hash, role FROM users WHERE email = :email;

-- UPDATE
UPDATE users
SET name = COALESCE(:name, name),
    role = COALESCE(:role, role)
WHERE id = :id
RETURNING id, email, name, role, created_at;

-- DELETE
DELETE FROM users WHERE id = :id RETURNING id;
