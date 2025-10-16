-- CREATE
INSERT INTO projects (owner_id, name)
VALUES (:owner_id, :name)
RETURNING id, owner_id, name, created_at;

-- READ
SELECT id, owner_id, name, created_at FROM projects WHERE id = :id;
SELECT id, owner_id, name, created_at
FROM projects
WHERE owner_id = :owner_id
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset;

-- UPDATE
UPDATE projects
SET name = COALESCE(:name, name)
WHERE id = :id AND owner_id = :owner_id
RETURNING id, owner_id, name, created_at;

-- DELETE
DELETE FROM projects
WHERE id = :id AND owner_id = :owner_id
RETURNING id;
