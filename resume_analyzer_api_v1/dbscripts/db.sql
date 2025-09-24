
select * from profiles p 
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the profiles table
-- id: Primary key for unique identification
-- profile_data: Stores the entire parsed JSON output from the LLM
-- embedding: Stores the vector embedding. The dimension (e.g., 768) depends on the embedding model.
--            Gemini's embedding-001 typically produces 768-dimensional vectors.
-- created_at: Timestamp for when the profile was added
-- CREATE TABLE IF NOT EXISTS profiles (
--     id SERIAL PRIMARY KEY,
--     profile_data JSONB NOT NULL,
--     embedding vector(768), -- Assuming embedding-001 model (768 dimensions)
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- Optional: Create indexes for efficient querying
-- GIN index on profile_data for fast JSONB queries (e.g., @>, ?, ?|)
CREATE INDEX IF NOT EXISTS idx_profiles_profile_data_gin ON profiles USING GIN (profile_data);

-- Indexes for specific fields within JSONB for faster direct filtering (e.g., name, company)
-- Using BTREE for scalar values extracted from JSONB
CREATE INDEX IF NOT EXISTS idx_profiles_name ON profiles ((profile_data->>'name'));
CREATE INDEX IF NOT EXISTS idx_profiles_summary ON profiles ((profile_data->>'summary'));

-- For semantic search, you'd typically create an IVFFlat or HNSW index on the 'embedding' column
-- after you have some data. This is done programmatically or after initial data load.
-- Example (don't run this until you have data and understand IVFFlat):
-- CREATE INDEX IF NOT EXISTS idx_profiles_embedding ON profiles USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
-- Or for cosine similarity:
-- CREATE INDEX IF NOT EXISTS idx_profiles_embedding_cosine ON profiles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- For now, we'll rely on the default index for vector search, which is less performant but works.



-- Profile tables
-- init_db.sql

-- Connect to the 'resume_db' database
\c defaultdb;

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the organizations table

CREATE TABLE IF NOT EXISTS organizations (
    id VARCHAR(255) PRIMARY KEY, -- Using VARCHAR for organization IDs like 'org123'
    name VARCHAR(255) NOT NULL,
    organization_type VARCHAR(255), -- NEW: Type of organization (e.g., 'Company', 'Recruitment Agency')
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255),      -- NEW: User ID or email of who created the organization
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- Add organization_type column
-- ALTER TABLE organizations
-- ADD COLUMN organization_type VARCHAR(255);

-- -- Add created_by column
-- ALTER TABLE organizations
-- ADD COLUMN created_by VARCHAR(255);

-- UPDATE organizations
-- SET
--     organization_type = 'OWN',  -- Example: 'Client', 'Vendor', 'Recruitment Agency'
--     created_by = 'test@test.com'         -- Example: 'system', 'john.doe@example.com'
-- WHERE
--     id = 'org123'; -- IMPORTANT: Replace 'org123' with the actual organization ID


CREATE TABLE IF NOT EXISTS agency_info (
    agencyOrgId VARCHAR(255) PRIMARY KEY, -- Primary key for the agency information
    orgId VARCHAR(255) NOT NULL,          -- The ID of the organization that this agency info is associated with
    created_by VARCHAR(255),              -- NEW: User ID or email of who created this agency info
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP

    -- Optional: Add a foreign key constraint to the organizations table
    -- This ensures that 'orgId' must refer to a valid 'id' in the 'organizations' table.
    -- Uncomment the line below if you want to enforce this referential integrity.
    -- FOREIGN KEY (orgId) REFERENCES organizations (id)
);

-- Optional: Add an index on orgId if you plan to frequently query by it
CREATE INDEX IF NOT EXISTS idx_agency_info_orgId ON agency_info (orgId);  
-- insert into agency_info values('org123','org123','test@test.com')
-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    firebase_uid VARCHAR(255) UNIQUE NOT NULL, -- Firebase User ID
    email VARCHAR(255) UNIQUE NOT NULL,
    organization_id VARCHAR(255) NOT NULL, -- Foreign key to organizations
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations (id)
);

-- Create the profiles table
CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    profile_data JSONB NOT NULL,      -- Stores the main LLM parsed JSON
    embedding vector(768),
    user_id INTEGER NOT NULL,         -- Links to the user who uploaded/owns it
    organization_id VARCHAR(255) NOT NULL, -- Links to the organization this profile belongs to
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (organization_id) REFERENCES organizations (id) -- Optional but good for integrity
);
-- Optional: Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_profiles_profile_data_gin ON profiles USING GIN (profile_data);
CREATE INDEX IF NOT EXISTS idx_profiles_name ON profiles ((profile_data->>'name'));
CREATE INDEX IF NOT EXISTS idx_profiles_summary ON profiles ((profile_data->>'summary'));

-- Optional: Add some initial data for testing authentication
INSERT INTO organizations (id, name, is_active) VALUES
('org123', 'Acme Corp', TRUE) ON CONFLICT (id) DO NOTHING;

-- For the user 'firebase_uid_user1', you'll need to replace 'firebase_uid_user1'
-- with an actual Firebase UID from your Firebase project's Authentication tab
-- after you create a test user (e.g., user@example.com).
-- Make sure this user is associated with 'org123' here.
INSERT INTO users (firebase_uid, email, organization_id, is_active) VALUES
('3LrX6uTxNlgbOM6Fn1FjvTCbwzx1', 'test@test.com', 'org123', TRUE) ON CONFLICT (firebase_uid) DO NOTHING;
-- Replace 'YOUR_FIREBASE_UID_USER1' with the actual UID from Firebase Console.

-- Add indexes for user_id and organization_id if you query by them frequently
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles (user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_organization_id ON profiles (organization_id);



-- 1. Create the roles table
-- Roles are specific to an organization (e.g., 'Admin' for Org A is different from 'Admin' for Org B)
CREATE TABLE IF NOT EXISTS roles (
    roleId VARCHAR(50) PRIMARY KEY, -- CHANGED: roleId (VARCHAR) as PK
    name VARCHAR(50) UNIQUE NOT NULL, -- e.g., 'ADMIN', 'RECRUITER', 'HIRING_MANAGER'
    description TEXT,
    created_by VARCHAR(255),          -- NEW: User ID or email of who created the role
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Already existed, confirmed
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);



CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id VARCHAR(50) NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),     
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(roleId) ON DELETE CASCADE
);


-- Optional: Add some initial roles
-- IMPORTANT: You must provide a roleId for each role now.
INSERT INTO roles (roleId, name, description, created_by) VALUES
('ADMIN', 'Admin', 'System Administrator with full access', 'system'),
('RECRUITER', 'Recruiter', 'Can upload, search, and filter profiles', 'system') ,
('HIRING_MANAGER', 'Hiring Manager', 'Can view profiles and review matches', 'system');

INSERT INTO user_roles (user_id, role_id, created_by) VALUES -- Added created_by here
((SELECT id FROM users WHERE firebase_uid = '3LrX6uTxNlgbOM6Fn1FjvTCbwzx1'), 'ADMIN', 'system')
ON CONFLICT (user_id, role_id) DO NOTHING;

-- 3. Create the resources table
-- Defines the items or functionalities that need access control (e.g., a specific UI menu item, a report, an API endpoint)
-- Enable the pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Existing tables (organizations, users, profiles, agency_info) remain the same.

-- Create the resources table for menu items, permissions, etc.
CREATE TABLE IF NOT EXISTS resources (
    id SERIAL PRIMARY KEY,
    resource_type VARCHAR(50) NOT NULL, -- e.g., 'MENU', 'PERMISSION', 'FEATURE'
    name VARCHAR(255) UNIQUE NOT NULL,  -- Name of the resource (e.g., 'Dashboard', 'Upload Profile', 'Admin Panel')
    display_name VARCHAR(255),          -- User-friendly display name
    path VARCHAR(255),                  -- URL path for menu items
    icon VARCHAR(255),                  -- Icon name for UI
    parent_id INTEGER,                  -- For hierarchical menus
    order_index INTEGER,                -- For sorting menu items
    is_active BOOLEAN DEFAULT TRUE,
    orgId VARCHAR(255),                 -- NEW: Organization ID for multi-tenancy of resources (NULL for global resources)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_id) REFERENCES resources(id), -- Self-referencing for hierarchy
    FOREIGN KEY (orgId) REFERENCES organizations(id) -- NEW: Foreign key to organizations table
);

-- Create indexes for efficient querying on resources
CREATE INDEX IF NOT EXISTS idx_resources_type ON resources (resource_type);
CREATE INDEX IF NOT EXISTS idx_resources_name ON resources (name);
CREATE INDEX IF NOT EXISTS idx_resources_parent_id ON resources (parent_id);
CREATE INDEX IF NOT EXISTS idx_resources_orgId ON resources (orgId); -- NEW: Index on orgId

-- Add a UNIQUE constraint for resource name and orgId if resources are unique per org
-- (e.g., each org has its own 'dashboard' resource, but there's also a global 'dashboard')
-- ALTER TABLE resources ADD CONSTRAINT UQ_resources_name_orgId UNIQUE (name, orgId);

-- Optional: Add some initial menu data for testing
-- IMPORTANT: You will need to add an 'orgId' for these if you want them to be specific to 'org123'
-- or leave orgId as NULL for global resources visible to all users (if your app supports global).
INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'dashboard_global', 'Dashboard', '/dashboard', 'fa-home', NULL, 1, TRUE, NULL) ON CONFLICT (name) DO nothing;
INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'analyise_profile_global', 'Analyse Profile', '/analyse-resume', 'fa-upload', NULL, 2, TRUE, NULL) ON CONFLICT (name) DO nothing;


INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'upload_profile_global', 'Upload Profile', '/upload-resume', 'fa-upload', NULL, 2, TRUE, NULL) ON CONFLICT (name) DO NOTHING;


INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'job_posting', 'Job Post', '/jobs', 'fa-upload', NULL, 2, TRUE, NULL) ON CONFLICT (name) DO NOTHING;


INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'candidates', 'Candidates', '/candidates', 'fa-upload', NULL, 2, TRUE, NULL) ON CONFLICT (name) DO NOTHING;


-- Existing INSERT statements for organizations and users (remember to update YOUR_FIREBASE_UID_USER1)
INSERT INTO organizations (id, name, organization_type, is_active, created_by) VALUES
('org123', 'Acme Corp', 'Client', TRUE, 'test@test.com') ON CONFLICT (id) DO NOTHING;

INSERT INTO users (firebase_uid, email, organization_id, is_active) VALUES
('YOUR_FIREBASE_UID_USER1', 'user@example.com', 'org123', TRUE) ON CONFLICT (firebase_uid) DO NOTHING;


-- 4. Create the permissions table
-- Defines generic actions that can be performed on resources
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,             -- e.g., 'view', 'edit', 'create', 'delete', 'manage', 'execute'
    description TEXT,                       -- Description of the permission
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name)                           -- Permissions are global and unique across the system
);

-- 5. Create the role_permissions junction table
-- This table defines which roles have which permissions on which resources.

CREATE TABLE IF NOT EXISTS role_permissions (
    roleid VARCHAR NOT NULL,
    permission_id INTEGER NOT NULL,
    resource_id INTEGER not NULL,               -- This is key: NULL means the permission applies to ALL resources of a given type, otherwise it's for a specific resource
    PRIMARY KEY (roleid, permission_id, resource_id), -- Composite key
    FOREIGN KEY (roleid) REFERENCES roles (roleid),
    FOREIGN KEY (permission_id) REFERENCES permissions (id),
    FOREIGN KEY (resource_id) REFERENCES resources (id)
);



-- DEFAULT VALUES ADMIN ROLE

-- 1. Ensure the 'execute' permission exists (if not already present)
INSERT INTO permissions (name, description, created_at)
VALUES ('execute', 'Ability to execute an API endpoint or perform an action', CURRENT_TIMESTAMP)
ON CONFLICT (name) DO NOTHING; -- Prevents errors if 'execute' permission already exists

INSERT INTO permissions (name, description, created_at)
VALUES ('manage', 'Ability to Manage an API endpoint or perform an action', CURRENT_TIMESTAMP)
ON CONFLICT (name) DO NOTHING; -- Prevents errors if 'execute' permission already exists

-- 2. Create the 'Admin' role for 'org123'
--    This will fail if an 'Admin' role already exists for 'org123' due to the UNIQUE constraint.
--    You might want to check for its existence first in a real application logic.
INSERT INTO roles (organization_id, name, description, created_at)
VALUES ('org123', 'Admin', 'Administrator role for organization org123', CURRENT_TIMESTAMP)
ON CONFLICT (organization_id, name) DO NOTHING;


-- Get the IDs for later use (assuming they were just inserted or already exist)
-- This is how you'd get the IDs programmatically, or you can hardcode them if you know them.
SELECT id INTO @admin_role_id FROM roles WHERE organization_id = 'org123' AND name = 'Admin';
SELECT id INTO @execute_permission_id FROM permissions WHERE name = 'execute';


-- 3. Define the API resources in the 'resources' table for 'org123'
--    These represent the specific API endpoints.
INSERT INTO resources (organization_id, name, resource_type, description, created_at)
VALUES
    ('org123', '/auth/profile/v2/upload_resume', 'API_Endpoint', 'API to upload resume (v2)', CURRENT_TIMESTAMP),
    ('org123', '/auth/profile/upload-resume', 'API_Endpoint', 'API to upload resume (legacy)', CURRENT_TIMESTAMP)
ON CONFLICT (organization_id, name) DO NOTHING; -- Prevents errors if resources already exist


-- Get the IDs for the newly created (or existing) resources
SELECT id INTO @v2_upload_resume_resource_id FROM resources WHERE organization_id = 'org123' AND name = '/auth/profile/v2/upload_resume';
SELECT id INTO @legacy_upload_resume_resource_id FROM resources WHERE organization_id = 'org123' AND name = '/auth/profile/upload-resume';


-- 4. Grant the 'execute' permission to the 'Admin' role for each specific API resource
--    This links the Admin role to the ability to execute these two APIs.


-- ADD RESOURCE TO ROLE - RESOURCE_ID available in resources table is added here
  
   INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
   
    (
		'ADMIN',
        (SELECT id FROM permissions WHERE name = 'execute'),
        (SELECT id FROM resources WHERE orgid = 'org123' AND name = 'job_posting')
    );


-- ASSIGN ROLE TO NEW USER WITH PERMISSIONS
INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
    (
		'ADMIN',
        (SELECT id FROM permissions WHERE name = 'execute'),
        (SELECT id FROM resources WHERE orgid = 'org123' AND name = 'candidates')
    ),
    (
		'ADMIN',
        (SELECT id FROM permissions WHERE name = 'execute'),
        (SELECT id FROM resources WHERE orgid = 'org123' AND name = 'analyise_profile_global')
    ),     
     (
		'ADMIN',
        (SELECT id FROM permissions WHERE name = 'execute'),
        (SELECT id FROM resources WHERE orgid = 'org123' AND name = 'upload_profile_global')
    ),
     (
        'ADMIN',
        (SELECT id FROM permissions WHERE name = 'execute'),
        (SELECT id FROM resources WHERE orgid = 'org123' AND name = 'dashboard_global')
    )

ON CONFLICT (roleid, permission_id, resource_id) DO NOTHING;

INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
   
    (
		'MANAGER',
        (SELECT id FROM permissions WHERE name = 'execute'),
        (SELECT id FROM resources WHERE orgid = 'org123' AND name = 'analyise_profile_global')
    ),     
     (
		'MANAGER',
        (SELECT id FROM permissions WHERE name = 'execute'),
        (SELECT id FROM resources WHERE orgid = 'org123' AND name = 'upload_profile_global')
    )

ON CONFLICT (roleid, permission_id, resource_id) DO NOTHING;



## NEW USER CREATION SCRIPTS
## NiXyxk7sVOXhq0tHerI28v6zxg02
INSERT INTO users (firebase_uid, email, organization_id, is_active) VALUES
('NiXyxk7sVOXhq0tHerI28v6zxg02', 'rahul.opengts@gmail.com', 'org123', TRUE) ON CONFLICT (firebase_uid) DO NOTHING;


INSERT INTO user_roles (user_id, role_id, created_by) VALUES -- Added created_by here
((SELECT id FROM users WHERE firebase_uid = 'NiXyxk7sVOXhq0tHerI28v6zxg02'), 'ADMIN', 'system')
ON CONFLICT (user_id, role_id) DO NOTHING;




INSERT INTO roles (roleId, name, description, created_by) VALUES
('MANAGER', 'Manager', 'Manger with few access', 'system');





UPDATE resources
SET
    path = '/analyse',         -- NEW path
    orgid = 'org123',   -- Optional: update display name
    updated_at = CURRENT_TIMESTAMP   -- Update timestamp
WHERE
    name = 'analyise_profile_global' 


UPDATE resources
SET
    path = '/dashboard',         -- NEW path
    orgid = 'org123',   -- Optional: update display name
    updated_at = CURRENT_TIMESTAMP   -- Update timestamp
WHERE
    name = 'dashboard_global' 

UPDATE resources
SET
    path = '/dashboard',         -- NEW path
    orgid = 'org123',   -- Optional: update display name
    updated_at = CURRENT_TIMESTAMP   -- Update timestamp
WHERE
    name = 'dashboard_global' 


UPDATE user_roles
SET
    role_id = 'MANAGER'
WHERE
    user_id = 3


-- ORGANIZATION
INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'analyise_profile_global', 'Analyse Profile', '/analyse-resume', 'fa-upload', NULL, 2, TRUE, 'ag123');


INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'upload_profile_global', 'Upload Profile', '/upload-resume', 'fa-upload', NULL, 2, TRUE, 'ag123') ;


INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'job_posting', 'Job Post', '/jobs', 'fa-upload', NULL, 2, TRUE, 'ag123')  ;


INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'candidates', 'Candidates', '/candidates', 'fa-upload', NULL, 2, TRUE, 'ag123') ;

INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
    (
		'MANAGER',
        3,
        20
    ),
    (
		'MANAGER',
        3,
        21
    ),     
     (
		'MANAGER',
        3,
        22
    ),
     (
        'MANAGER',
        3,
        23
    )

