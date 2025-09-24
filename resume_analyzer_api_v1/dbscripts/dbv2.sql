-- public.agency_info definition

-- Drop table

-- DROP TABLE public.agency_info;

CREATE TABLE public.agency_info (
	agencyorgid varchar(255) NOT NULL,
	orgid varchar(255) NOT NULL,
	created_by varchar(255) NULL,
	created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT agency_info_pkey PRIMARY KEY (agencyorgid,orgid)
);
CREATE INDEX idx_agency_info_orgid ON public.agency_info USING btree (orgid);


-- public.organizations definition

-- Drop table

-- DROP TABLE public.organizations;

CREATE TABLE public.organizations (
	id varchar(255) NOT NULL,
	"name" varchar(255) NOT NULL,
	is_active bool NULL DEFAULT true,
	created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	organization_type varchar(255) NULL,
	created_by varchar(255) NULL,
	CONSTRAINT organizations_pkey PRIMARY KEY (id)
);

-- public.permissions definition

-- Drop table

-- DROP TABLE public.permissions;

CREATE TABLE public.permissions (
	id serial4 NOT NULL,
	"name" varchar(255) NOT NULL,
	description text NULL,
	created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT permissions_name_key UNIQUE (name),
	CONSTRAINT permissions_pkey PRIMARY KEY (id)
);


-- public.profiles definition

-- Drop table

-- DROP TABLE public.profiles;

CREATE TABLE public.profiles (
	id serial4 NOT NULL,
	profile_data jsonb NOT NULL,
	embedding public.vector NULL,
	user_id int4 NOT NULL,
	organization_id varchar(255) NOT NULL,
	created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT profiles_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_profiles_organization_id ON public.profiles USING btree (organization_id);
CREATE INDEX idx_profiles_user_id ON public.profiles USING btree (user_id);


-- public.profiles foreign keys

ALTER TABLE public.profiles ADD CONSTRAINT profiles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);
ALTER TABLE public.profiles ADD CONSTRAINT profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);



-- Add the filebatchid column to the profiles table to link to a bulk upload batch
ALTER TABLE profiles ADD COLUMN filebatchid UUID;

-- Optional: Add an index for faster lookups if you plan to query by this ID
CREATE INDEX idx_profiles_filebatchid ON profiles (filebatchid);

-- Add jd_organization_type and parent_org_id to the profiles table
ALTER TABLE public.profiles ADD COLUMN jd_organization_type VARCHAR(50);
ALTER TABLE public.profiles ADD COLUMN parent_org_id VARCHAR(255) NULL;

-- Optional: Add a foreign key constraint for parent_org_id for data integrity
ALTER TABLE public.profiles
ADD CONSTRAINT fk_profile_parent_org_id
FOREIGN KEY (parent_org_id) REFERENCES public.organizations(id) ON DELETE SET NULL;
CREATE INDEX idx_profiles_parent_org_id ON public.profiles (parent_org_id);


-- public.resources definition

-- Drop table

-- DROP TABLE public.resources;

CREATE TABLE public.resources (
	id serial4 NOT NULL,
	resource_type varchar(50) NOT NULL,
	"name" varchar(255) NOT NULL,
	display_name varchar(255) NULL,
	"path" varchar(255) NULL,
	icon varchar(255) NULL,
	parent_id int4 NULL,
	order_index int4 NULL,
	is_active bool NULL DEFAULT true,
	orgid varchar(255) NULL,
	created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	-- CONSTRAINT resources_name_key UNIQUE (name),
	CONSTRAINT resources_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_resources_name ON public.resources USING btree (name);
CREATE INDEX idx_resources_orgid ON public.resources USING btree (orgid);
CREATE INDEX idx_resources_parent_id ON public.resources USING btree (parent_id);
CREATE INDEX idx_resources_type ON public.resources USING btree (resource_type);


-- public.resources foreign keys

ALTER TABLE public.resources ADD CONSTRAINT resources_orgid_fkey FOREIGN KEY (orgid) REFERENCES public.organizations(id);
ALTER TABLE public.resources ADD CONSTRAINT resources_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.resources(id);


-- public.role_permissions definition

-- Drop table

-- DROP TABLE public.role_permissions;

CREATE TABLE public.role_permissions (
	roleid varchar NOT NULL,
	permission_id int4 NOT NULL,
	resource_id int4 NOT NULL,
	CONSTRAINT role_permissions_pkey PRIMARY KEY (roleid, permission_id, resource_id)
);


-- public.role_permissions foreign keys

ALTER TABLE public.role_permissions ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id);
ALTER TABLE public.role_permissions ADD CONSTRAINT role_permissions_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES public.resources(id);
ALTER TABLE public.role_permissions ADD CONSTRAINT role_permissions_roleid_fkey FOREIGN KEY (roleid) REFERENCES public.roles(roleid);


-- public.roles definition

-- Drop table

-- DROP TABLE public.roles;

CREATE TABLE public.roles (
	roleid varchar(50) NOT NULL,
	"name" varchar(50) NOT NULL,
	description text NULL,
	created_by varchar(255) NULL,
	created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT roles_name_key UNIQUE (name),
	CONSTRAINT roles_pkey PRIMARY KEY (roleid)
);

-- public.user_roles definition

-- Drop table

-- DROP TABLE public.user_roles;

CREATE TABLE public.user_roles (
	user_id int4 NOT NULL,
	role_id varchar(50) NOT NULL,
	assigned_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	created_by varchar(255) NULL,
	CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id)
);


-- public.user_roles foreign keys

ALTER TABLE public.user_roles ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(roleid) ON DELETE CASCADE;
ALTER TABLE public.user_roles ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

-- public.users definition

-- Drop table

-- DROP TABLE public.users;

CREATE TABLE public.users (
	id serial4 NOT NULL,
	firebase_uid varchar(255) NOT NULL,
	email varchar(255) NOT NULL,
	organization_id varchar(255) NOT NULL,
	is_active bool NULL DEFAULT true,
	created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT users_email_key UNIQUE (email),
	CONSTRAINT users_firebase_uid_key UNIQUE (firebase_uid),
	CONSTRAINT users_pkey PRIMARY KEY (id)
);


-- public.users foreign keys

ALTER TABLE public.users ADD CONSTRAINT users_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


-- JD
-- Create the job_descriptions table
-- Create the job_descriptions table
CREATE TABLE IF NOT EXISTS job_descriptions (
    id SERIAL PRIMARY KEY,
    job_details JSONB NOT NULL,
    embedding vector(768),
    organization_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    user_tags JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    jd_version INTEGER DEFAULT 1,             -- NEW: Field for JD version, default to 1
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (organization_id) REFERENCES organizations (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);
ALTER TABLE job_descriptions ADD COLUMN jd_organization_type VARCHAR(50);


CREATE INDEX IF NOT EXISTS idx_jd_org_id ON job_descriptions (organization_id);
CREATE INDEX IF NOT EXISTS idx_jd_user_id ON job_descriptions (user_id);
CREATE INDEX IF NOT EXISTS idx_jd_job_details_gin ON job_descriptions USING GIN (job_details);
CREATE INDEX IF NOT EXISTS idx_jd_user_tags_gin ON job_descriptions USING GIN (user_tags);
CREATE INDEX IF NOT EXISTS idx_jd_is_active ON job_descriptions (is_active);
CREATE INDEX IF NOT EXISTS idx_jd_version ON job_descriptions (jd_version); -- NEW: Index on jd_version

ALTER TABLE job_descriptions ADD COLUMN parent_org_id VARCHAR(255) NULL;

-- Optional: Add a foreign key constraint for data integrity
ALTER TABLE job_descriptions
ADD CONSTRAINT fk_jd_parent_org_id
FOREIGN KEY (parent_org_id) REFERENCES organizations(id) ON DELETE SET NULL;

-- Optional: Add a composite index if you frequently query by orgId AND name AND version
-- For example, to uniquely identify a JD version within an organization
-- CREATE UNIQUE INDEX IF NOT EXISTS uq_jd_org_name_version ON job_descriptions (organization_id, (job_details->>'job_title'), jd_version);

-- (Include all your existing CREATE TABLE and INSERT statements for other tables here)
-- ALTER SCRIPT FOR JOB-DESCRIPTION-
-- alter_job_descriptions_table.sql
\c resume_db;
ALTER TABLE job_descriptions ADD COLUMN user_tags JSONB DEFAULT '[]'::jsonb;
ALTER TABLE job_descriptions ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
-- If you don't have updated_at, add it too
ALTER TABLE job_descriptions ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
CREATE INDEX IF NOT EXISTS idx_jd_user_tags_gin ON job_descriptions USING GIN (user_tags);
CREATE INDEX IF NOT EXISTS idx_jd_is_active ON job_descriptions (is_active);

ALTER TABLE job_descriptions ADD COLUMN jd_version INTEGER DEFAULT 1;
CREATE INDEX IF NOT EXISTS idx_jd_version ON job_descriptions (jd_version);
-- If you want all existing JDs to have version 1:
-- UPDATE job_descriptions SET jd_version = 1 WHERE jd_version IS NULL;

-----------------------

-- GIN index for JSONB queries on job_details
CREATE INDEX IF NOT EXISTS idx_jd_job_details_gin ON job_descriptions USING GIN (job_details);
-- For semantic search (HNSW/IVFFlat index will be needed later, or done via Python as in profile_repository)
-- CREATE INDEX IF NOT EXISTS idx_jd_embedding_cosine ON job_descriptions USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);



CREATE EXTENSION IF NOT EXISTS vector;
-- Enable uuid-ossp extension for UUID generation if not already enabled (PostgreSQL specific)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the job_profile_match table
CREATE TABLE IF NOT EXISTS job_profile_match (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), -- Self-generated UUID as PK
    job_id INTEGER NOT NULL,
    profile_id INTEGER NOT NULL,
    candidate_name VARCHAR(255) NOT NULL,
    overall_score NUMERIC(5,2) NOT NULL, -- Numeric for score (e.g., 99.99)
    match_results_json JSONB NOT NULL,   -- JSON field holding detailed results
    organization_id VARCHAR(255) NOT NULL, -- Org to which the job belongs
    agency_id VARCHAR(255),               -- Agency org ID, if applicable (can be NULL)
    created_by VARCHAR(255) NOT NULL,     -- User who initiated the match
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (job_id) REFERENCES job_descriptions (id),
    FOREIGN KEY (profile_id) REFERENCES profiles (id),
    FOREIGN KEY (organization_id) REFERENCES organizations (id),
    FOREIGN KEY (agency_id) REFERENCES organizations (id) -- Optional: FK to agency org
);

-- Create indexes for fast searching
CREATE INDEX IF NOT EXISTS idx_jpm_job_id ON job_profile_match (job_id);
CREATE INDEX IF NOT EXISTS idx_jpm_profile_id ON job_profile_match (profile_id);
CREATE INDEX IF NOT EXISTS idx_jpm_candidate_name ON job_profile_match (candidate_name); -- For candidate name search
CREATE INDEX IF NOT EXISTS idx_jpm_overall_score ON job_profile_match (overall_score DESC); -- For ordering by score
CREATE INDEX IF NOT EXISTS idx_jpm_organization_id ON job_profile_match (organization_id);
CREATE INDEX IF NOT EXISTS idx_jpm_agency_id ON job_profile_match (agency_id);
CREATE INDEX IF NOT EXISTS idx_jpm_job_org_score ON job_profile_match (job_id, organization_id, overall_score DESC); -- Composite for common search

-- (Include all your existing CREATE TABLE and INSERT statements for other tables here)



-- Enable UUID generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the new table to track bulk uploads
CREATE TABLE bulk_profile_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(1024) NOT NULL,
    status VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,
    organization_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user
        FOREIGN KEY(user_id) 
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_organization
        FOREIGN KEY(organization_id) 
        REFERENCES organizations(id)
        ON DELETE CASCADE
);

-- Create indexes for faster lookups
CREATE INDEX idx_bulk_profile_uploads_filename ON bulk_profile_uploads(filename);
CREATE INDEX idx_bulk_profile_uploads_user_id ON bulk_profile_uploads(user_id);
CREATE INDEX idx_bulk_profile_uploads_organization_id ON bulk_profile_uploads(organization_id);
CREATE INDEX idx_bulk_profile_uploads_status ON bulk_profile_uploads(status);


-- Step 1: Add the job_id column to the bulk_profile_uploads table
ALTER TABLE bulk_profile_uploads ADD COLUMN job_id INTEGER;

-- Step 2 (Recommended): Add a foreign key constraint to link to the job_descriptions table.
-- This ensures that every job_id in this table corresponds to a real job.
ALTER TABLE bulk_profile_uploads
ADD CONSTRAINT fk_bulk_upload_job_id
FOREIGN KEY (job_id)
REFERENCES job_descriptions(id)
ON DELETE SET NULL;
