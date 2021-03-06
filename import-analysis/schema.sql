BEGIN;
DROP TABLE IF EXISTS "network_comp" CASCADE;
DROP TABLE IF EXISTS "network_page" CASCADE;
DROP TABLE IF EXISTS "network_langlink" CASCADE;
DROP TABLE IF EXISTS "network_pagelink" CASCADE;
DROP TABLE IF EXISTS "network_categorylink" CASCADE;
DROP TABLE IF EXISTS "network_path" CASCADE;
DROP TABLE IF EXISTS "network_pageposition" CASCADE;
DROP TABLE IF EXISTS "network_pagemeaning" CASCADE;

CREATE TABLE "network_comp" (
    "key" varchar(36) NOT NULL PRIMARY KEY,
    "namespace" integer NOT NULL,
    "coherent" boolean NULL,
    "size" integer NULL
)
;
CREATE TABLE "network_page" (
    "key" varchar(32) NOT NULL PRIMARY KEY,
    "lang" varchar(16) NOT NULL,
    "namespace" integer NOT NULL,
    "title" varchar(1024) NOT NULL,
    "redirect_id" varchar(32) NULL,
    "comp_id" varchar(36) NULL REFERENCES "network_comp" ("key") DEFERRABLE INITIALLY DEFERRED
)
;
ALTER TABLE "network_page" ADD CONSTRAINT redirect_id_refs_key_4cdda70b FOREIGN KEY ("redirect_id") REFERENCES "network_page" ("key") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "network_langlink" (
    "id" serial NOT NULL PRIMARY KEY,
    "src_id" varchar(32) NOT NULL REFERENCES "network_page" ("key") DEFERRABLE INITIALLY DEFERRED,
    "dst_id" varchar(32) NOT NULL REFERENCES "network_page" ("key") DEFERRABLE INITIALLY DEFERRED,
    "comp_id" varchar(36) NULL REFERENCES "network_comp" ("key") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "network_pagelink" (
    "id" serial NOT NULL PRIMARY KEY,
    "src_id" varchar(32) NOT NULL REFERENCES "network_page" ("key") DEFERRABLE INITIALLY DEFERRED,
    "dst_id" varchar(32) NOT NULL REFERENCES "network_page" ("key") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "network_categorylink" (
    "id" serial NOT NULL PRIMARY KEY,
    "page_id" varchar(32) NOT NULL REFERENCES "network_page" ("key") DEFERRABLE INITIALLY DEFERRED,
    "category_id" varchar(32) NOT NULL REFERENCES "network_page" ("key") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "network_path" (
    "id" serial NOT NULL PRIMARY KEY,
    "src_id" varchar(32) NOT NULL REFERENCES "network_page" ("key") DEFERRABLE INITIALLY DEFERRED,
    "dst_id" varchar(32) NOT NULL REFERENCES "network_page" ("key") DEFERRABLE INITIALLY DEFERRED,
    "length" integer NOT NULL,
    "serialized" text NOT NULL,
    "comp_id" varchar(36) NOT NULL REFERENCES "network_comp" ("key") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "network_pageposition" (
    "id" serial NOT NULL PRIMARY KEY,
    "page_id" varchar(32) NOT NULL REFERENCES "network_page" ("key") DEFERRABLE INITIALLY DEFERRED,
    "x" double precision NULL,
    "y" double precision NULL,
    "z" double precision NULL,
    "comp_id" varchar(36) NOT NULL REFERENCES "network_comp" ("key") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "network_pagemeaning" (
    "id" serial NOT NULL PRIMARY KEY,
    "auth" varchar(30) NOT NULL,
    "page_id" varchar(32) NOT NULL REFERENCES "network_page" ("key") DEFERRABLE INITIALLY DEFERRED,
    "meaning" varchar(36) NOT NULL,
    "comp_id" varchar(36) NOT NULL REFERENCES "network_comp" ("key") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE INDEX "network_page_redirect_id" ON "network_page" ("redirect_id");
CREATE INDEX "network_page_comp_id" ON "network_page" ("comp_id");
CREATE INDEX "network_langlink_src_id" ON "network_langlink" ("src_id");
CREATE INDEX "network_langlink_dst_id" ON "network_langlink" ("dst_id");
CREATE INDEX "network_langlink_comp_id" ON "network_langlink" ("comp_id");
CREATE INDEX "network_pagelink_src_id" ON "network_pagelink" ("src_id");
CREATE INDEX "network_pagelink_dst_id" ON "network_pagelink" ("dst_id");
CREATE INDEX "network_categorylink_page_id" ON "network_categorylink" ("page_id");
CREATE INDEX "network_categorylink_category_id" ON "network_categorylink" ("category_id");
CREATE INDEX "network_path_src_id" ON "network_path" ("src_id");
CREATE INDEX "network_path_dst_id" ON "network_path" ("dst_id");
CREATE INDEX "network_path_comp_id" ON "network_path" ("comp_id");
CREATE INDEX "network_pageposition_page_id" ON "network_pageposition" ("page_id");
CREATE INDEX "network_pageposition_comp_id" ON "network_pageposition" ("comp_id");
CREATE INDEX "network_pagemeaning_auth" ON "network_pagemeaning" ("auth");
CREATE INDEX "network_pagemeaning_page_id" ON "network_pagemeaning" ("page_id");
CREATE INDEX "network_pagemeaning_comp_id" ON "network_pagemeaning" ("comp_id");

CREATE INDEX "network_page_lang_title" ON "network_page" ("lang", "title");
CREATE INDEX "network_page_title_upper" ON "network_page" USING BTREE (UPPER(title) VARCHAR_PATTERN_OPS);
COMMIT;
