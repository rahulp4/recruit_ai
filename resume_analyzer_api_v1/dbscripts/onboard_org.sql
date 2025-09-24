-- ag123 is Agency having org789 and ng123 under it.
-- txt123 and org123 are indepedent

INSERT INTO organizations (id, name, organization_type, is_active, created_by) VALUES
('ag123', 'Agency HR', 'AGENCY', TRUE, 'system') ON CONFLICT (id) DO nothing;

INSERT INTO organizations (id, name, organization_type, is_active, created_by) VALUES
('txt123', 'Txt4Parts Org', 'OWN', TRUE, 'system') ON CONFLICT (id) DO nothing;

INSERT INTO organizations (id, name, organization_type, is_active, created_by) VALUES
('ng123', 'Neural Grid', 'OWN', TRUE, 'system') ON CONFLICT (id) DO nothing;


INSERT INTO agency_info (agencyOrgId, orgId, created_by) VALUES
('ag123', 'org789', 'system') ON CONFLICT (agencyOrgId, orgId) DO nothing;

INSERT INTO agency_info (agencyOrgId, orgId, created_by) VALUES
('ag123', 'ng123', 'system') ON CONFLICT (agencyOrgId, orgId) DO NOTHING;


## NEW MENU

INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'candidate_search', 'Search', '/candidate-search', 'fa-upload', NULL, 2, TRUE, 'org123') ;
INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
    (
		'MANAGER',
        2,
        28
    )

## Adding Candidate Search to ag123 and MANAGER
INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'candidate_search', 'Search', '/candidate-search', 'fa-upload', NULL, 2, TRUE, 'ag123') ;

INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
    (
		'MANAGER',
        2,
        31
    )


## Assing to ROLE a new resoource like MENU
INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
    (
		'ADMIN',
        2,
        28
    )    

## ADDING DASHBOARD MENUT TO NEW USER rahul.open -3 
    INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'dashboard_global', 'Search', '/dashboard', 'fa-upload', NULL, 1, TRUE, 'ag123') ;

    
    INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
    (
		'MANAGER',
        3,
        30
    )    

//BulkUploadPage
INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'bulk_upload', 'Bulk Upload', '/bulk-upload', 'fa-upload-bulk', NULL, 2, TRUE, 'org123') ;
INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
    (
		'MANAGER',
        2,
        29
    )

//BulkUploadPage MANAGER ag123
        INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgId) VALUES
('MENU', 'bulk_upload', 'Bulk Upload', '/bulk-upload', 'fa-upload-bulk', NULL, 2, TRUE, 'ag123') ;
INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
    (
		'MANAGER',
        2,
        33
    )

INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
    (
		'ADMIN',
        2,
        29
    )    



    -- DELETE DATA ORDER

    delete from job_profile_match jpm 
    delete from profiles p2
    delete from bulk_profile_uploads 

create a new repo named UserPrivisioningRepo which do following
1. Inserts following  
into    resources tale created_at and updated_at should be current time
    
INSERT INTO public.resources
(id, resource_type, "name", display_name, "path", icon, parent_id, order_index, is_active, orgid, created_at, updated_at)
VALUES(4, 'MENU', 'upload_profile_global', 'Upload Profile', '/upload-resume', 'fa-upload', NULL, 2, true, 'organizationId', '2025-06-13 20:46:36.582', '2025-06-13 22:32:34.075');

INSERT INTO public.resources
(id, resource_type, "name", display_name, "path", icon, parent_id, order_index, is_active, orgid, created_at, updated_at)
VALUES(1, 'MENU', 'dashboard_global', 'Dashboard', '/dashboard', 'fa-home', NULL, 1, true, 'organizationId', '2025-06-13 20:45:21.361', '2025-06-13 20:45:21.361');

INSERT INTO public.resources
(id, resource_type, "name", display_name, "path", icon, parent_id, order_index, is_active, orgid, created_at, updated_at)
VALUES(5, 'MENU', 'job_posting', 'Job Post', '/jobs', 'fa-upload', NULL, 2, true, 'organizationId', '2025-06-13 22:35:29.582', '2025-06-13 22:35:29.582');

INSERT INTO public.resources
(id, resource_type, "name", display_name, "path", icon, parent_id, order_index, is_active, orgid, created_at, updated_at)
VALUES(28, 'MENU', 'candidate_search', 'Search', '/candidate-search', 'fa-upload', NULL, 2, true, 'organizationId', '2025-07-01 22:10:06.249', '2025-07-01 22:10:06.249');

INSERT INTO public.resources
(id, resource_type, "name", display_name, "path", icon, parent_id, order_index, is_active, orgid, created_at, updated_at)
VALUES(29, 'MENU', 'bulk_upload', 'Bulk Upload', '/bulk-upload', 'fa-upload-bulk', NULL, 2, true, 'organizationId', '2025-07-05 17:40:35.766', '2025-07-05 17:40:35.766');


For each of the above inserts , take the resourceid from id field generated and insert into role_permissions as 
id - is the user id generated for new user in user table 
    INSERT INTO role_permissions (roleid, permission_id, resource_id)
VALUES
    (
		'MANAGER',
        8,
        28
    )  