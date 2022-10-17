CREATE USER pynotes WITH PASSWORD 'pynotes';
create database pynotes with owner = pynotes ENCODING = 'UTF8';
CREATE SCHEMA AUTHORIZATION pynotes;
create table pynotes.note (
    id SERIAL PRIMARY KEY,
    uri TEXT UNIQUE NOT NULL,
    sentence_embeddings BYTEA
);
