BEGIN;
CREATE TABLE "network_comp" (
    "key" varchar(36) NOT NULL PRIMARY KEY,
    "namespace" integer NOT NULL,
    "coherent" boolean,
    "size" integer
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
CREATE INDEX "network_page_redirect_id" ON "network_page" ("redirect_id");
CREATE INDEX "network_page_comp_id" ON "network_page" ("comp_id");
CREATE INDEX "network_langlink_src_id" ON "network_langlink" ("src_id");
CREATE INDEX "network_langlink_dst_id" ON "network_langlink" ("dst_id");
CREATE INDEX "network_langlink_comp_id" ON "network_langlink" ("comp_id");
CREATE INDEX "network_pagelink_src_id" ON "network_pagelink" ("src_id");
CREATE INDEX "network_pagelink_dst_id" ON "network_pagelink" ("dst_id");
CREATE INDEX "network_categorylink_page_id" ON "network_categorylink" ("page_id");
CREATE INDEX "network_categorylink_category_id" ON "network_categorylink" ("category_id");

CREATE INDEX "network_page_lang_title" ON "network_page" ("lang", "title");
CREATE INDEX "network_page_title_upper" ON "network_page" USING BTREE (UPPER(title) VARCHAR_PATTERN_OPS);
COMMIT;

