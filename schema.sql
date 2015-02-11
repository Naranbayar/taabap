/* drop table IF EXISTS news; */
create table IF NOT EXISTS news (
  id integer primary key autoincrement,
  url text,
  origin text,
  title text,
  origin_url text,
  content text,
  time text,
  image text,
  read integer,
  published integer
);
