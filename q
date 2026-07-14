[33mcommit 9908eb99367a9b96f2bd53559b641a29a8228aac[m[33m ([m[1;36mHEAD -> [m[1;32mmain[m[33m, [m[1;31morigin/main[m[33m, [m[1;31morigin/HEAD[m[33m)[m
Author: Charanreddy2408 <akepatisricharan@gmail.com>
Date:   Fri Jul 10 14:04:59 2026 +0530

    feat: add visit cancellation functionality with new endpoint and response model

[33mcommit 4df999a7916b02c576645f3cd020b79757f6561d[m
Merge: 6393003 d507df5
Author: Charanreddy2408 <akepatisricharan@gmail.com>
Date:   Thu Jul 9 13:27:35 2026 +0530

    Merge branch 'main' of https://github.com/DebuggingDork/ShineGold-Backend

[33mcommit d507df53d02b03ae3cb0440a6021fd4874dfacd4[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jul 9 13:03:46 2026 +0530

    feat: integrate visit form functionality with new endpoints and models for enhanced visit management

[33mcommit a81906da71f54a174c6ab00b7c24bb0603711c50[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jul 9 12:23:15 2026 +0530

    feat: enhance farm executive assignment management with new relationships and assignment logic

[33mcommit adefe7fcaf038d9e0cc21cf0246ba7e677bbd203[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jul 9 11:45:42 2026 +0530

    feat: implement proximity-based farm assignment invitations and acceptance endpoints

[33mcommit 63930033e8d36f7d0431bf385a9946558cb6aa7b[m
Author: Charanreddy2408 <akepatisricharan@gmail.com>
Date:   Thu Jul 9 11:11:22 2026 +0530

    docs: update README for local setup instructions and environment variables; enhance .env.example with specific values; add CORS middleware to FastAPI app; modify user response structure in user router

[33mcommit 49c30bcc64ca925327304264bd40bcb4408cf941[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 12:26:29 2026 +0530

    feat: add farm visit history and latest visit record endpoints

[33mcommit 62a970cf86936bcf7468f6bcab10c88a43530e2e[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 12:26:29 2026 +0530

    feat: enrich visit history summaries and full record detail

[33mcommit b61e79dc14155aaa7622f78f0ee6201be7380ea2[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 12:26:29 2026 +0530

    feat: support more mobile audio formats for visit voice notes

[33mcommit 39cb130bdcab18a709107495aef068acc94cc1cd[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 12:23:00 2026 +0530

    feat: add setup-location endpoint and onboarding flag on login

[33mcommit af7e78b9aef3cf6e3d4e425db5696a7f198c921c[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 12:22:54 2026 +0530

    feat: require address in bulk import and add home location setup

[33mcommit 2a1683f709f36bae282c4fd06ed14efcc4bf5d23[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 12:22:45 2026 +0530

    feat: add address to executive create and requires_location_setup flag

[33mcommit 8fc6a495a2765d7d75ae3393f2e06e3ebaf31cfe[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 12:06:50 2026 +0530

    feat: add transfer-farms, bulk-import, and import template endpoints

[33mcommit 398dc4589588592b7a24348d162909e595d344d6[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 12:06:44 2026 +0530

    feat: add farm transfer and bulk executive import services

[33mcommit 59d7def169cc3afe1236dcecd949ba9782208af9[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 12:06:38 2026 +0530

    feat: add farm transfer and bulk import response schemas

[33mcommit 985b594934e581bffcdd8e1dac685fd865ba3e6b[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 12:06:30 2026 +0530

    chore: add openpyxl for executive bulk import

[33mcommit 2402c693e92c4f79389bb0c664a0248baae6a58e[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:52:43 2026 +0530

    refactor: reuse UserService for executive assignment validation

[33mcommit 9cfee9b6f3323030e90d429d37fb7150d031b445[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:52:37 2026 +0530

    feat: add PATCH /users/{user_id}/block and route create through UserService

[33mcommit 37ea71d101c1d1eb27bff8175d9589ec7c852f80[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:52:32 2026 +0530

    feat: add forgot-password and admin reset approval endpoints

[33mcommit 1a4364421f4232075f865f8474498549b08a2ce0[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:51:44 2026 +0530

    feat: add user and password reset services for business logic

[33mcommit f2324f7c066c7c43a584712a9854622391fa3f9b[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:51:34 2026 +0530

    feat: add password reset repository for data access

[33mcommit 246253047c308ddccd886599f23aa5853c79ca67[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:51:30 2026 +0530

    feat: add password reset and user block response schemas

[33mcommit 0c65590510236f129ea3afd103392489f161d683[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:51:26 2026 +0530

    feat: add shared HTTP error helpers for consistent API responses

[33mcommit 36c5eb952f6aea54e735107009b05fb1e4f0e1d1[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:48:31 2026 +0530

    feat: add POST /users and GET /users/{user_id} endpoints

[33mcommit 9ce94feb6492ab2e7b6d7b830ef064f98588096a[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:48:27 2026 +0530

    feat: add executive detail query and mapper to user repository

[33mcommit ac99223577d3803fba2362e1aa4b11eddfb7d3e6[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:48:24 2026 +0530

    feat: add user create and executive detail response schemas

[33mcommit f472f4d25fca76d1a2c1f4b8b1b1c40b66acbe9f[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:45:32 2026 +0530

    feat: add GET /dashboard/executive and GET /users endpoints

[33mcommit 3c86c5f83db8c577adcd455559735ac6b301af68[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:45:29 2026 +0530

    feat: add executive dashboard stats and executive list with counts

[33mcommit 543ff143ee09cfd48eb05f87b33f81f705387e9b[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:45:24 2026 +0530

    feat: add executive dashboard and user list response schemas

[33mcommit 4c333ac190a908e50bb4c08e8ba442ab2486e6f1[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:44:07 2026 +0530

    chore: register harvests and dashboard routers

[33mcommit 0c1a3fdd8badc38e2c55fc518fffde7920e0645d[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:44:03 2026 +0530

    feat: add GET /harvests/calendar and GET /dashboard/admin endpoints

[33mcommit 513c4f5be0d0e8df90c104502edacbd1e8d42daa[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:43:55 2026 +0530

    feat: add harvest calendar and admin dashboard query logic

[33mcommit 674ac02e6e4a773131e0268986e554f06cd9d345[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:43:52 2026 +0530

    feat: add harvest calendar and admin dashboard response schemas

[33mcommit 110711c7dcce9d1d207b0abb5b8feaec30a1e8a2[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:42:16 2026 +0530

    chore: register farmers router in FastAPI app

[33mcommit 910beb51332a45a9a597972644fb160cc4da4fb8[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:42:12 2026 +0530

    feat: add GET /farmers and GET /farmers/{farmer_id} endpoints

[33mcommit 755b530474174cc8ae1b62d08ab2a9a42bb15d8c[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:42:08 2026 +0530

    feat: add farmer repository with list, get-by-id, and mappers

[33mcommit 5f1f06b537b35d2ba9e862f8678624c0d43c18c1[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:41:54 2026 +0530

    feat: add farmer list and detail response schemas

[33mcommit 738ccc7881aaf156091675a36ea8ce7bfc9cce67[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:40:56 2026 +0530

    feat: add GET /visits/mine and GET /visits/{visit_id} endpoints

[33mcommit 9fbe15b84a10700849dd400e78336ce3a0578fe2[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:40:52 2026 +0530

    feat: add list_mine query and visit detail mapping to repository

[33mcommit 3e99ddf0901125b7a4a55102919e2f271cb54cfe[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:40:49 2026 +0530

    feat: add visit mine list and detail response schemas

[33mcommit 287aa80e7980853d4386ee8316417dc33f51fead[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:39:42 2026 +0530

    feat: add PATCH /visits/{visit_id}/form and POST /visits/{visit_id}/submit

[33mcommit b42c37a2e1e2baa92195b0d3a0ac228d9da40f29[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:39:38 2026 +0530

    feat: add visit form update and submit logic to repository

[33mcommit 6c5968b3bc594ce3928edce745413e3474cb1040[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:39:33 2026 +0530

    feat: add VisitFormResponse schema for visit form updates

[33mcommit 138cd44782e558b619c50ba3ce2efbca2a8f12cb[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:37:52 2026 +0530

    feat: add POST /api/v1/visits/checkin and register visits router

[33mcommit df38bf8ba6b2b732436c6afbe85f7e97824b5c2c[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:37:49 2026 +0530

    feat: add visit repository for check-in flow

[33mcommit 71eb9625e4db52fe6e9975fb473f58a918d4032c[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:37:45 2026 +0530

    feat: add PATCH /api/v1/farms/{farm_id}/assign endpoint

[33mcommit 3ef7f14fddf349aec5743b381678a3d0ad8c1ae1[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:37:42 2026 +0530

    feat: add FarmAssignOut schema for executive reassignment

[33mcommit f20a3ec0bf46b0304e80b05aceb2558895ed2661[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:34:43 2026 +0530

    feat: add GET and PATCH /api/v1/farms/{farm_id} endpoints

[33mcommit d89888bfee072ccb05ec8ee0b7c1c2e0825dc247[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:34:38 2026 +0530

    feat: add farm get-by-id, detail mapping, and update to repository

[33mcommit 8a8a89a9c43832e09824a20f5375b65a6cdfe35a[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:34:33 2026 +0530

    feat: add farm detail, visit log, and update schemas

[33mcommit 8ad17b033451333f3ac22f284088503304dc31db[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:31:22 2026 +0530

    chore: register farms router in FastAPI app

[33mcommit a53ef4b89cfecbc7b40d56308b948497c5f48c1d[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:31:17 2026 +0530

    feat: add POST and GET /api/v1/farms endpoints

[33mcommit a73060d9ef8f952b72b03b424879f5568fc5265d[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:31:11 2026 +0530

    feat: add farm repository for onboard and filtered listing

[33mcommit e396829381e661bfd6d87cade151e860a907769e[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:31:05 2026 +0530

    feat: update farm schemas for onboard response and list items

[33mcommit 60712987513deb86a5e2af44f064b4c7db3bdd96[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:31:00 2026 +0530

    feat: add shared PaginatedResponse schema for list endpoints

[33mcommit 75c118b60542256126fbd49a9dd3d8d3bb13115d[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:25:47 2026 +0530

    feat: add profile and file upload endpoints
    
    Wire GET/PATCH /users/me with visit and onboarding stats, expose POST /uploads/presign via StorageService, and move profile off the auth /me test route.

[33mcommit 21a9c24920751ee290cffeed2b12f5586dff834d[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Sun Jul 5 11:22:41 2026 +0530

    feat: add API status documentation for Executive and Super Admin apps, detailing implemented and pending endpoints

[33mcommit 006193a2fe3823f5712ad8cb27e8ea8974897224[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 14:57:39 2026 +0530

    feat: add asyncpg connection arguments to settings for improved database compatibility

[33mcommit fa03c1c2db1e4caf62d48297d1fd00ee0020029a[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 14:44:47 2026 +0530

    chore: remove seed_admin script due to passlib incompatibility with bcrypt

[33mcommit 9086bab29924b7e252ecb511c4a83ef32bf26394[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 14:34:14 2026 +0530

    refactor: rchange the fike name from core/dependency to dependencies

[33mcommit 9d3db8ea79e3980a466651df714ac81a36ccf99b[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 14:30:04 2026 +0530

    chore: update FastAPI dependency to include standard extras to use uv run fastapi dev command

[33mcommit 29375750e7d6e4f03550e51767dc109e7781ec92[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 14:26:15 2026 +0530

    fix: replace passlib with bcrypt for password hashing to resolve compatibility issues

[33mcommit 4e60b38c62abfbb9476f719d2a7fef124f3efc14[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 14:20:21 2026 +0530

    chore: add seed script for initial super admin user

[33mcommit abc30a19a9dcd1fdae189127c0514a6d86783786[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 14:19:32 2026 +0530

    feat: mount auth router in main app

[33mcommit 305effa3d09f83df2cdcc3f89978ce72fade62b6[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 14:18:53 2026 +0530

    feat: implement authentication routes including login, logout, password change, token refresh, and user retrieval

[33mcommit 64a24c80485d969e76dfbfe526dfb530aeea58fd[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 14:17:04 2026 +0530

    feat: implement user authentication and authorization dependencies with role-based access control

[33mcommit 2f05f9a155843086b0a1a24f310f1f6d988f11ff[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 14:15:43 2026 +0530

    feat: add GPS coordinates to user and visit photo models, and enforce unique constraint on visit MCQ answers

[33mcommit 9c2b47336013f62d218a7dfc34cbbb4b94499fc3[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 14:02:13 2026 +0530

    feat: add Alembic migration for users, farms, farmers, visits tables and document common issues with Supabase integration

[33mcommit 1b718f599ef7730fc475475ab073ef201d6a9708[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 13:24:29 2026 +0530

    docs: document common issues and solutions for Alembic connection to Supabase

[33mcommit 806960748e31be45dfbad5be8e0643500b9dc983[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 13:15:05 2026 +0530

    feat: add initial migration for users, farms, farmers, visits

[33mcommit 5903d6f4872592749f5c0689c923209c66458ad4[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 13:15:04 2026 +0530

    fix: correct Supabase pooler URLs for Windows DNS and special-char passwords

[33mcommit 7634067cdd0c4b0be820d3b6e59dcad36c159f8e[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:39:51 2026 +0530

    fix: wire Alembic env to async direct URL and model metadata

[33mcommit ee2d4a8c1aa28a069a3b710198cb13b8c01265e5[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:39:37 2026 +0530

    fix: normalize DATABASE_URL_DIRECT to asyncpg driver

[33mcommit 13dd2122e5869ae3a35ff46540228074b13b1d0d[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:37:32 2026 +0530

    docs: update README with instructions for running alembic after database design changes

[33mcommit 2d6cc398b9827f505fa320c6577392d1ac481f76[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:36:07 2026 +0530

    feat: add Supabase Storage service for presigned upload urls

[33mcommit 95bdfb31b1cfbe3806407b6dcbd62fb646ef7738[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:35:16 2026 +0530

    feat: add AuthService for login, refresh, change-password logic

[33mcommit 6da0d56ff932dc4ecc0c54138434891b18ffc676[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:34:44 2026 +0530

    feat: add JWT and password hashing utilities

[33mcommit a95fe61adde31d071cab0b320b1649874e62a5c5[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:33:59 2026 +0530

    feat: add UserRepository with query methods

[33mcommit a5eb43613c8a4dc3653b8ae7ed98843db7ec21a8[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:32:59 2026 +0530

    feat: add Pydantic schemas for visit management including check-in, check-out, and visit updates

[33mcommit 62c5cb576d0fed94386e6768b498f5638e9d2268[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:32:32 2026 +0530

    feat: add Pydantic schemas for farm and farmer management including creation, output, and update models

[33mcommit 02361c74fabafc2bd7071d6849dfd8ad6414f974[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:32:07 2026 +0530

    feat: add Pydantic schemas for authentication including login, token management, and password reset

[33mcommit 699c9a057aa3c75854990a31a36c67854fe115e0[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:31:41 2026 +0530

    feat: implement Pydantic schemas for user management including creation, update, and output models

[33mcommit c249be1b3a9ea1f4d6363c42b5b1cfedb6669ba0[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:30:50 2026 +0530

    feat: add User, Farm, Farmer, Visit SQLAlchemy models with enums

[33mcommit 1f85859cb361a191fe3e52e7ae65f6d57c757f3b[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:24:25 2026 +0530

    fix: point alembic to settings-based direct db url instead of static config

[33mcommit c9d7c461cb8864b03723d3688b0d07f602a8b87a[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:22:46 2026 +0530

    chore: initialize alembic with async template

[33mcommit 33583e517e6df6804ad88a774a49c64a80ee7186[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:17:51 2026 +0530

    feat: add minimal app entrypoint with health check route

[33mcommit 689c4429e6e7940fce58d9d8a7f80a914429077f[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:16:54 2026 +0530

    feat: add async db session and declarative base

[33mcommit fe68f2473986ad36417032587f740a2cf86014c5[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:16:12 2026 +0530

    feat: add pydantic settings config loader

[33mcommit 22d1aaf92d95f9754882d62f96715bc501b76a10[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 12:14:31 2026 +0530

    chore: remove unused main.py file from backend

[33mcommit 93be2f799fea93434a51ed30476090ab597bd367[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 11:48:09 2026 +0530

    chore: add .env.example with supabase config keys

[33mcommit 055326edd7cf7a1b7bf51fd8e648e8748d63e857[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 11:42:26 2026 +0530

    chore: update .gitignore to organize sections and remove Flutter-related entries

[33mcommit 7dde0914d96ac75e9e3781f863fe04c541c781d3[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 11:36:31 2026 +0530

    chore: scaffold app package structure with repositories layer

[33mcommit cc5ab45e459c18c0fb2386511aef590d3a7bc34a[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 11:32:04 2026 +0530

    chore: add dev dependencies (pytest, ruff)

[33mcommit 7c4f81ce02693caed48f5df56eb580a0a28fcabb[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 11:30:14 2026 +0530

    chore: add .gitignore and update dependencies in pyproject.toml

[33mcommit 12449088639ce929c448a99f8f69e92fdee1b2b8[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 11:24:38 2026 +0530

    chore: initialize uv project

[33mcommit b84ae58bf5f08221a5625ca07225d199fd6498ac[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 11:18:03 2026 +0530

    Add backend API specification for ShineGold app

[33mcommit 2755afc4a37e618f156e2cc18900f787207b8f77[m
Author: Kisanlink <mani.m@kisanlink.in>
Date:   Thu Jun 25 11:13:42 2026 +0530

    First commit buddy
