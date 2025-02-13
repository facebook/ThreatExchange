# MySQL hash-lookup examples

The MIH code in `../cpp` can be used for PDQ-hash lookups. An alternative is to implement a hamming-distance SQL function. The example here has been tested with mysql 14.14.

NOTE: Also check out the int64 examples in bottom half of this README. Preliminary tests using the int64 hash for similarity computations have shown a 5x performance boost.

## Create table

```
CREATE DATABASE pdq;
USE pdq;

CREATE TABLE hamming_test(
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
  hash VARCHAR(64) NOT NULL,
  metadata  VARCHAR(64),
  CONSTRAINT mypk PRIMARY KEY (id)
);

DESCRIBE hamming_test;
+----------+----------------------+------+-----+---------+----------------+
| Field    | Type                 | Null | Key | Default | Extra          |
+----------+----------------------+------+-----+---------+----------------+
| id       | smallint(5) unsigned | NO   | PRI | NULL    | auto_increment |
| hash     | varchar(64)          | NO   |     | NULL    |                |
| metadata | varchar(64)          | YES  |     | NULL    |                |
+----------+----------------------+------+-----+---------+----------------+
```

## Populate table

```
$ pdq-photo-hasher $(lsr \*.jpg \*.png)
f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22,./dih/bridge-1-original.jpg
b0a10efd71cc3f429413d48d0ffffe12e34e0e17ada952a9d29684210aa9e5af,./dih/bridge-2-rotate-90.jpg
adad5a64b5a142e55362a09057dacd5ae63b847fc23794b766b319361fc93188,./dih/bridge-3-rotate-180.jpg
a5f4a457a48995e8c9065c275aaa5498b61ba4bdf8fcf80387c32f8b0bfc4f05,./dih/bridge-4-rotate-270.jpg
f8f80f31e0f417b00e37f5cd028f980fb36ed02a9662c1e233e6cc634e9c64dd,./dih/bridge-5-flipx.jpg
8dad2599b1a1bd1853625f6553da32a1e63b7280c2374b4866b366c91bc9ce77,./dih/bridge-6-flipy.jpg
f0a1f102f1dcc0bd9c5309720fff018de34ef1e8ada9a956d2967ade0ea91a50,./dih/bridge-7-flip-plus-1.jpg
a5f05ba8a4896a17c106a3da5aaaab07b61b5b42f8fc07fc83c3d0740bfcb0fa,./dih/bridge-8-flip-minus-1.jpg
f439d924da56a1d4c63973a56acfc926cd53d9341b18367d318666cf9b142649,./exif-rotn/exif-rotn-1.jpg
3acfa3cfab36b95e39cfa0023946790af441f1417d850401f7616005ffc17ff2,./exif-rotn/exif-rotn-3.jpg
e9782aad54ae0b6365315ac278592d68d4b5434a5fcd7471f7abcb594b481a94,./exif-rotn/exif-rotn-6.jpg
6b507c23b4adb07ec2fe2b4db52038b15e0c970fcaf3f049058ae8687bf9251e,./exif-rotn/exif-rotn-8.jpg
54a977c221d14c1c43ba5e4e21d4a13989a3553f1462611cbb87fda7be83b677,./labelme-subset/q0003.jpg
992d44af36d69e6ca6b812485928bac11def254ef539ac6d07466c9abcc65b92,./labelme-subset/q0004.jpg
cfb2009ddd21c6dab0846a7745b5984757a8a4535b3377aea2591d32b33ff840,./labelme-subset/q0122.jpg
a0fe94f1e5cc1cc8dd855948498dc9243f7ca27336f036d7f212b74bc103c9a7,./labelme-subset/q0291.jpg
3049d96239e24d4dca2c55512b8b9b77425f4dbcf575a0a95555aaab5554aaaa,./labelme-subset/q0746.jpg
489db672e9190276d452aeab41eba20f02375fe4092d88defdf491a5c55c5f70,./labelme-subset/q1050.jpg
b150231ffae4710ffcf4f18bb574b109a576f14bb8543189f8743289f174b109,./labelme-subset/q2821.jpg
1f811b9d2e7fbc6613c0c3f30e041f9df69b836303e10f067fcdfc12c02d01f9,./pen-and-coaster.png
```

```
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22', 'dih/bridge-1-original.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'b0a10efd71cc3f429413d48d0ffffe12e34e0e17ada952a9d29684210aa9e5af', 'dih/bridge-2-rotate-90.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'adad5a64b5a142e55362a09057dacd5ae63b847fc23794b766b319361fc93188', 'dih/bridge-3-rotate-180.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'a5f4a457a48995e8c9065c275aaa5498b61ba4bdf8fcf80387c32f8b0bfc4f05', 'dih/bridge-4-rotate-270.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'f8f80f31e0f417b00e37f5cd028f980fb36ed02a9662c1e233e6cc634e9c64dd', 'dih/bridge-5-flipx.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '8dad2599b1a1bd1853625f6553da32a1e63b7280c2374b4866b366c91bc9ce77', 'dih/bridge-6-flipy.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'f0a1f102f1dcc0bd9c5309720fff018de34ef1e8ada9a956d2967ade0ea91a50', 'dih/bridge-7-flip-plus-1.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'a5f05ba8a4896a17c106a3da5aaaab07b61b5b42f8fc07fc83c3d0740bfcb0fa', 'dih/bridge-8-flip-minus-1.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'f439d924da56a1d4c63973a56acfc926cd53d9341b18367d318666cf9b142649', 'exif-rotn/exif-rotn-1.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '3acfa3cfab36b95e39cfa0023946790af441f1417d850401f7616005ffc17ff2', 'exif-rotn/exif-rotn-3.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'e9782aad54ae0b6365315ac278592d68d4b5434a5fcd7471f7abcb594b481a94', 'exif-rotn/exif-rotn-6.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '6b507c23b4adb07ec2fe2b4db52038b15e0c970fcaf3f049058ae8687bf9251e', 'exif-rotn/exif-rotn-8.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '54a977c221d14c1c43ba5e4e21d4a13989a3553f1462611cbb87fda7be83b677', 'labelme-subset/q0003.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '992d44af36d69e6ca6b812485928bac11def254ef539ac6d07466c9abcc65b92', 'labelme-subset/q0004.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'cfb2009ddd21c6dab0846a7745b5984757a8a4535b3377aea2591d32b33ff840', 'labelme-subset/q0122.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'a0fe94f1e5cc1cc8dd855948498dc9243f7ca27336f036d7f212b74bc103c9a7', 'labelme-subset/q0291.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '3049d96239e24d4dca2c55512b8b9b77425f4dbcf575a0a95555aaab5554aaaa', 'labelme-subset/q0746.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '489db672e9190276d452aeab41eba20f02375fe4092d88defdf491a5c55c5f70', 'labelme-subset/q1050.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, 'b150231ffae4710ffcf4f18bb574b109a576f14bb8543189f8743289f174b109', 'labelme-subset/q2821.jpg');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '1f811b9d2e7fbc6613c0c3f30e041f9df69b836303e10f067fcdfc12c02d01f9', 'pen-and-coaster.png');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000000000000000ffffffffffffffff0000000000000001fffffffffffffffe', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000000000000001000000000000000200000000000000040000000000000008', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000000000000010000000000000002000000000000000400000000000000080', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000000000000100000000000000020000000000000004000000000000000800', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000000000001000000000000000200000000000000040000000000000008000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000000000010000000000000002000000000000000400000000000000080000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000000000100000000000000020000000000000004000000000000000800000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000000001000000000000000200000000000000040000000000000008000000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000000010000000000000002000000000000000400000000000000080000000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000000100000000000000020000000000000004000000000000000800000000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000001000000000000000200000000000000040000000000000008000000000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000010000000000000002000000000000000400000000000000080000000000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0000100000000000000020000000000000004000000000000000800000000000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0001000000000000000200000000000000040000000000000008000000000000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0010000000000000002000000000000000400000000000000080000000000000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '0100000000000000020000000000000004000000000000000800000000000000', 'test-pattern');
INSERT INTO hamming_test (id, hash, metadata) VALUES (NULL, '1000000000000000200000000000000040000000000000008000000000000000', 'test-pattern');
```

```
select * from hamming_test;
+----+------------------------------------------------------------------+-------------------------------+
| id | hash                                                             | metadata                      |
+----+------------------------------------------------------------------+-------------------------------+
|  1 | f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22 | dih/bridge-1-original.jpg     |
|  2 | b0a10efd71cc3f429413d48d0ffffe12e34e0e17ada952a9d29684210aa9e5af | dih/bridge-2-rotate-90.jpg    |
|  3 | adad5a64b5a142e55362a09057dacd5ae63b847fc23794b766b319361fc93188 | dih/bridge-3-rotate-180.jpg   |
|  4 | a5f4a457a48995e8c9065c275aaa5498b61ba4bdf8fcf80387c32f8b0bfc4f05 | dih/bridge-4-rotate-270.jpg   |
|  5 | f8f80f31e0f417b00e37f5cd028f980fb36ed02a9662c1e233e6cc634e9c64dd | dih/bridge-5-flipx.jpg        |
|  6 | 8dad2599b1a1bd1853625f6553da32a1e63b7280c2374b4866b366c91bc9ce77 | dih/bridge-6-flipy.jpg        |
|  7 | f0a1f102f1dcc0bd9c5309720fff018de34ef1e8ada9a956d2967ade0ea91a50 | dih/bridge-7-flip-plus-1.jpg  |
|  8 | a5f05ba8a4896a17c106a3da5aaaab07b61b5b42f8fc07fc83c3d0740bfcb0fa | dih/bridge-8-flip-minus-1.jpg |
|  9 | f439d924da56a1d4c63973a56acfc926cd53d9341b18367d318666cf9b142649 | exif-rotn/exif-rotn-1.jpg     |
| 10 | 3acfa3cfab36b95e39cfa0023946790af441f1417d850401f7616005ffc17ff2 | exif-rotn/exif-rotn-3.jpg     |
| 11 | e9782aad54ae0b6365315ac278592d68d4b5434a5fcd7471f7abcb594b481a94 | exif-rotn/exif-rotn-6.jpg     |
| 12 | 6b507c23b4adb07ec2fe2b4db52038b15e0c970fcaf3f049058ae8687bf9251e | exif-rotn/exif-rotn-8.jpg     |
| 13 | 54a977c221d14c1c43ba5e4e21d4a13989a3553f1462611cbb87fda7be83b677 | labelme-subset/q0003.jpg      |
| 14 | 992d44af36d69e6ca6b812485928bac11def254ef539ac6d07466c9abcc65b92 | labelme-subset/q0004.jpg      |
| 15 | cfb2009ddd21c6dab0846a7745b5984757a8a4535b3377aea2591d32b33ff840 | labelme-subset/q0122.jpg      |
| 16 | a0fe94f1e5cc1cc8dd855948498dc9243f7ca27336f036d7f212b74bc103c9a7 | labelme-subset/q0291.jpg      |
| 17 | 3049d96239e24d4dca2c55512b8b9b77425f4dbcf575a0a95555aaab5554aaaa | labelme-subset/q0746.jpg      |
| 18 | 489db672e9190276d452aeab41eba20f02375fe4092d88defdf491a5c55c5f70 | labelme-subset/q1050.jpg      |
| 19 | b150231ffae4710ffcf4f18bb574b109a576f14bb8543189f8743289f174b109 | labelme-subset/q2821.jpg      |
| 20 | 1f811b9d2e7fbc6613c0c3f30e041f9df69b836303e10f067fcdfc12c02d01f9 | pen-and-coaster.png           |
| 21 | 0000000000000000ffffffffffffffff0000000000000001fffffffffffffffe | test-pattern                  |
| 22 | 0000000000000001000000000000000200000000000000040000000000000008 | test-pattern                  |
| 23 | 0000000000000010000000000000002000000000000000400000000000000080 | test-pattern                  |
| 24 | 0000000000000100000000000000020000000000000004000000000000000800 | test-pattern                  |
| 25 | 0000000000001000000000000000200000000000000040000000000000008000 | test-pattern                  |
| 26 | 0000000000010000000000000002000000000000000400000000000000080000 | test-pattern                  |
| 27 | 0000000000100000000000000020000000000000004000000000000000800000 | test-pattern                  |
| 28 | 0000000001000000000000000200000000000000040000000000000008000000 | test-pattern                  |
| 29 | 0000000010000000000000002000000000000000400000000000000080000000 | test-pattern                  |
| 30 | 0000000100000000000000020000000000000004000000000000000800000000 | test-pattern                  |
| 31 | 0000001000000000000000200000000000000040000000000000008000000000 | test-pattern                  |
| 32 | 0000010000000000000002000000000000000400000000000000080000000000 | test-pattern                  |
| 33 | 0000100000000000000020000000000000004000000000000000800000000000 | test-pattern                  |
| 34 | 0001000000000000000200000000000000040000000000000008000000000000 | test-pattern                  |
| 35 | 0010000000000000002000000000000000400000000000000080000000000000 | test-pattern                  |
| 36 | 0100000000000000020000000000000004000000000000000800000000000000 | test-pattern                  |
| 37 | 1000000000000000200000000000000040000000000000008000000000000000 | test-pattern                  |
+----+------------------------------------------------------------------+-------------------------------+
```

## Create stored function for Hamming distance on 256-bit hex-encoded hashes

```
-- This is Hamming distance, i.e. bit-count of XOR, on pairs of hex-encoded 256-bit hashes.
-- MySQL has built-in XOR on 16-bit words via the ^ operator, and built-in bit_count.
-- So this function is simply:
-- * Splitting 256-bit hex-encoded hashes into quadruples of 64-bit hex-encoded words;
-- * Converting to 64-bit integer;
-- * Bit-count of wordwise XORs;
-- * Summing those up.
DELIMITER |
CREATE FUNCTION HAMMING_DISTANCE_256(ha VARCHAR(64), hb VARCHAR(64))
  RETURNS INT
  DETERMINISTIC
  BEGIN
    DECLARE ha0 VARCHAR(16);
    DECLARE ha1 VARCHAR(16);
    DECLARE ha2 VARCHAR(16);
    DECLARE ha3 VARCHAR(16);

    DECLARE hb0 VARCHAR(16);
    DECLARE hb1 VARCHAR(16);
    DECLARE hb2 VARCHAR(16);
    DECLARE hb3 VARCHAR(16);

    DECLARE d0 INT;
    DECLARE d1 INT;
    DECLARE d2 INT;
    DECLARE d3 INT;

    SET ha0 = SUBSTRING(ha,  1, 16);
    SET ha1 = SUBSTRING(ha, 17, 16);
    SET ha2 = SUBSTRING(ha, 33, 16);
    SET ha3 = SUBSTRING(ha, 49, 16);

    SET hb0 = SUBSTRING(hb,  1, 16);
    SET hb1 = SUBSTRING(hb, 17, 16);
    SET hb2 = SUBSTRING(hb, 33, 16);
    SET hb3 = SUBSTRING(hb, 49, 16);

    SET d0 = BIT_COUNT(CAST(CONV(ha0, 16, 10) AS UNSIGNED) ^ CAST(CONV(hb0, 16, 10) AS UNSIGNED));
    SET d1 = BIT_COUNT(CAST(CONV(ha1, 16, 10) AS UNSIGNED) ^ CAST(CONV(hb1, 16, 10) AS UNSIGNED));
    SET d2 = BIT_COUNT(CAST(CONV(ha2, 16, 10) AS UNSIGNED) ^ CAST(CONV(hb2, 16, 10) AS UNSIGNED));
    SET d3 = BIT_COUNT(CAST(CONV(ha3, 16, 10) AS UNSIGNED) ^ CAST(CONV(hb3, 16, 10) AS UNSIGNED));

    RETURN d0 + d1 + d2 + d3;
    RETURN 999;
  END|
DELIMITER ;
```

```
SELECT HAMMING_DISTANCE_256("f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22", "f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b23");
```

## Search for hashes

```
SELECT * FROM hamming_test WHERE HAMMING_DISTANCE_256(hash, "f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b23") < 32;
+----+------------------------------------------------------------------+---------------------------+
| id | hash                                                             | metadata                  |
+----+------------------------------------------------------------------+---------------------------+
|  1 | f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22 | dih/bridge-1-original.jpg |
+----+------------------------------------------------------------------+---------------------------+

SELECT * FROM hamming_test WHERE HAMMING_DISTANCE_256(hash, "f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b23") < 256;
+----+------------------------------------------------------------------+-------------------------------+
| id | hash                                                             | metadata                      |
+----+------------------------------------------------------------------+-------------------------------+
|  1 | f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22 | dih/bridge-1-original.jpg     |
|  2 | b0a10efd71cc3f429413d48d0ffffe12e34e0e17ada952a9d29684210aa9e5af | dih/bridge-2-rotate-90.jpg    |
|  3 | adad5a64b5a142e55362a09057dacd5ae63b847fc23794b766b319361fc93188 | dih/bridge-3-rotate-180.jpg   |
|  4 | a5f4a457a48995e8c9065c275aaa5498b61ba4bdf8fcf80387c32f8b0bfc4f05 | dih/bridge-4-rotate-270.jpg   |
|  5 | f8f80f31e0f417b00e37f5cd028f980fb36ed02a9662c1e233e6cc634e9c64dd | dih/bridge-5-flipx.jpg        |
|  6 | 8dad2599b1a1bd1853625f6553da32a1e63b7280c2374b4866b366c91bc9ce77 | dih/bridge-6-flipy.jpg        |
|  7 | f0a1f102f1dcc0bd9c5309720fff018de34ef1e8ada9a956d2967ade0ea91a50 | dih/bridge-7-flip-plus-1.jpg  |
|  8 | a5f05ba8a4896a17c106a3da5aaaab07b61b5b42f8fc07fc83c3d0740bfcb0fa | dih/bridge-8-flip-minus-1.jpg |
|  9 | f439d924da56a1d4c63973a56acfc926cd53d9341b18367d318666cf9b142649 | exif-rotn/exif-rotn-1.jpg     |
| 10 | 3acfa3cfab36b95e39cfa0023946790af441f1417d850401f7616005ffc17ff2 | exif-rotn/exif-rotn-3.jpg     |
| 11 | e9782aad54ae0b6365315ac278592d68d4b5434a5fcd7471f7abcb594b481a94 | exif-rotn/exif-rotn-6.jpg     |
| 12 | 6b507c23b4adb07ec2fe2b4db52038b15e0c970fcaf3f049058ae8687bf9251e | exif-rotn/exif-rotn-8.jpg     |
| 13 | 54a977c221d14c1c43ba5e4e21d4a13989a3553f1462611cbb87fda7be83b677 | labelme-subset/q0003.jpg      |
| 14 | 992d44af36d69e6ca6b812485928bac11def254ef539ac6d07466c9abcc65b92 | labelme-subset/q0004.jpg      |
| 15 | cfb2009ddd21c6dab0846a7745b5984757a8a4535b3377aea2591d32b33ff840 | labelme-subset/q0122.jpg      |
| 16 | a0fe94f1e5cc1cc8dd855948498dc9243f7ca27336f036d7f212b74bc103c9a7 | labelme-subset/q0291.jpg      |
| 17 | 3049d96239e24d4dca2c55512b8b9b77425f4dbcf575a0a95555aaab5554aaaa | labelme-subset/q0746.jpg      |
| 18 | 489db672e9190276d452aeab41eba20f02375fe4092d88defdf491a5c55c5f70 | labelme-subset/q1050.jpg      |
| 19 | b150231ffae4710ffcf4f18bb574b109a576f14bb8543189f8743289f174b109 | labelme-subset/q2821.jpg      |
| 20 | 1f811b9d2e7fbc6613c0c3f30e041f9df69b836303e10f067fcdfc12c02d01f9 | pen-and-coaster.png           |
| 21 | 0000000000000000ffffffffffffffff0000000000000001fffffffffffffffe | test-pattern                  |
| 22 | 0000000000000001000000000000000200000000000000040000000000000008 | test-pattern                  |
| 23 | 0000000000000010000000000000002000000000000000400000000000000080 | test-pattern                  |
| 24 | 0000000000000100000000000000020000000000000004000000000000000800 | test-pattern                  |
| 25 | 0000000000001000000000000000200000000000000040000000000000008000 | test-pattern                  |
| 26 | 0000000000010000000000000002000000000000000400000000000000080000 | test-pattern                  |
| 27 | 0000000000100000000000000020000000000000004000000000000000800000 | test-pattern                  |
| 28 | 0000000001000000000000000200000000000000040000000000000008000000 | test-pattern                  |
| 29 | 0000000010000000000000002000000000000000400000000000000080000000 | test-pattern                  |
| 30 | 0000000100000000000000020000000000000004000000000000000800000000 | test-pattern                  |
| 31 | 0000001000000000000000200000000000000040000000000000008000000000 | test-pattern                  |
| 32 | 0000010000000000000002000000000000000400000000000000080000000000 | test-pattern                  |
| 33 | 0000100000000000000020000000000000004000000000000000800000000000 | test-pattern                  |
| 34 | 0001000000000000000200000000000000040000000000000008000000000000 | test-pattern                  |
| 35 | 0010000000000000002000000000000000400000000000000080000000000000 | test-pattern                  |
| 36 | 0100000000000000020000000000000004000000000000000800000000000000 | test-pattern                  |
| 37 | 1000000000000000200000000000000040000000000000008000000000000000 | test-pattern                  |
+----+------------------------------------------------------------------+-------------------------------+
```

# Examples using Int64 Hashes

Preliminary experiments using sets of 4 int64 vals to represent the hashes instead of hex strings has shown to boost performance by 5x.

Below are analogous MySQL examples using the Set-of-4-int64-vals hash representations.


## Create table

We are still using the pdq database as in the hex string hash examples.
However, we will use a different table for the int64 values.

```
CREATE TABLE hamming_test_int64(
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
  hash1 BIGINT(16) NOT NULL,
  hash2 BIGINT(16) NOT NULL,
  hash3 BIGINT(16) NOT NULL,
  hash4 BIGINT(16) NOT NULL,
  quality smallint(3) NOT NULL,
  metadata  VARCHAR(64),
  CONSTRAINT mypk PRIMARY KEY (id)
);

DESCRIBE hamming_test_int64;
+----------+----------------------+------+-----+---------+----------------+
| Field    | Type                 | Null | Key | Default | Extra          |
+----------+----------------------+------+-----+---------+----------------+
| id       | smallint(5) unsigned | NO   | PRI | NULL    | auto_increment |
| hash1    | bigint(16)           | NO   |     | NULL    |                |
| hash2    | bigint(16)           | NO   |     | NULL    |                |
| hash3    | bigint(16)           | NO   |     | NULL    |                |
| hash4    | bigint(16)           | NO   |     | NULL    |                |
| quality  | smallint(3)          | NO   |     | NULL    |                |
| metadata | varchar(64)          | YES  |     | NULL    |                |
+----------+----------------------+------+-----+---------+----------------+
```

## Populate table

Note that we are calling the pdq-photo-hasher command from the parent directory (/ThreatExchange-PDQ), which is where we placed the executable file /lsr for this example.

```
$ ./cpp/pdq-photo-hasher --int64 $(./lsr \*.jpg \*.png)
7072692243309524172,-5778998286441671213,8188330764704884818,3806149485627632429,100,./data/misc-images/wee.jpg
-506390186751121329,447837829151548400,-5517420998596354531,3739874024492931874,100,./data/misc-images/b.jpg
-1851883412434831230,-517366565115992180,-6982379065928243982,-5196839458248216476,100,./data/misc-images/c.png
1970457985089599,35748417275625727,143835907860923391,287953294993589247,0,./data/misc-images/small.jpg
5232538946727641718,-3147261139009953265,159701744806103262,-147332746629587088,100,./data/reg-test-input/labelme-subset/q1050.jpg
-7409190292624597396,-6433371965755966783,2156983767585631341,524225818483121042,4,./data/reg-test-input/labelme-subset/q0004.jpg
-5669993310599220977,-219284899487239927,-6523761702682218103,-543754086962122487,100,./data/reg-test-input/labelme-subset/q2821.jpg
6100538845924772892,4880316835877396793,-8528879539896295140,-4933695969863420297,3,./data/reg-test-input/labelme-subset/q0003.jpg
3479551203021573453,-3878631371961558153,4782626803258073257,6149008519092021930,100,./data/reg-test-input/labelme-subset/q0746.jpg
-6845870616893186872,-2484481452418414300,4574709937228232407,-1003538230961518169,100,./data/reg-test-input/labelme-subset/q0291.jpg
-3480718883984128294,-5727335765605246905,6316479155306461102,-6748330463045093312,100,./data/reg-test-input/labelme-subset/q0122.jpg
-1623500741728662685,7291709062978809194,-3119513180237368207,-600162540948284780,100,./data/reg-test-input/exif-rotn/exif-rotn-6.jpg
4237785886704974174,4165724403810072842,-5457816009823681535,-621109694718443534,100,./data/reg-test-input/exif-rotn/exif-rotn-3.jpg
-848408302477467180,-4163169226228512474,-3651336055051241859,3568652796583749193,100,./data/reg-test-input/exif-rotn/exif-rotn-1.jpg
7732817052992123262,-4396028573784196943,6776957633371041865,399387052429878558,100,./data/reg-test-input/exif-rotn/exif-rotn-8.jpg
985485235504397594,6008460953880507045,-1856763424508785848,7400371626640526967,100,./data/reg-test-input/dih/bridge-6-flipy.jpg
-506390186751121329,447837829151548400,-5517420998596354531,3739874024492931874,100,./data/reg-test-input/dih/bridge-1-original.jpg
-5931985745586601241,6585002181338499418,-1856744737106062153,7400286332884955528,100,./data/reg-test-input/dih/bridge-3-rotate-180.jpg
-6489587382679410153,-3961299772108002553,-5324561791232243716,-8663852061026373382,100,./data/reg-test-input/dih/bridge-8-flip-minus-1.jpg
3504098466769681730,-8064868805366514606,-2067699684055887191,-3272281701943220817,100,./data/reg-test-input/dih/bridge-2-rotate-90.jpg
-1106230730686676803,-7758848447041567859,-2067449197268194986,-3272292983748617648,100,./data/reg-test-input/dih/bridge-7-flip-plus-1.jpg
-6489506366711294488,-3961377498131180392,-5324480998602377213,-8664028983614222587,100,./data/reg-test-input/dih/bridge-4-rotate-270.jpg
-506638251177273422,1024557701110142991,-5517243612152020510,3739760529982121181,100,./data/reg-test-input/dih/bridge-5-flipx.jpg
2270126048941161574,-7800014707879567459,-820918045774901498,9209293970506318329,100,./data/reg-test-input/pen-and-coaster.png
```
```
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, 2270126048941161574,-7800014707879567459,-820918045774901498,9209293970506318329,100,'./data/reg-test-input/pen-and-coaster.png');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -506390186751121329,447837829151548400,-5517420998596354531,3739874024492931874,100,'./data/misc-images/b.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -1851883412434831230,-517366565115992180,-6982379065928243982,-5196839458248216476,100,'./data/misc-images/c.png');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, 1970457985089599,35748417275625727,143835907860923391,287953294993589247,0,'./data/misc-images/small.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, 5232538946727641718,-3147261139009953265,159701744806103262,-147332746629587088,100,'./data/reg-test-input/labelme-subset/q1050.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -7409190292624597396,-6433371965755966783,2156983767585631341,524225818483121042,4,'./data/reg-test-input/labelme-subset/q0004.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -5669993310599220977,-219284899487239927,-6523761702682218103,-543754086962122487,100,'./data/reg-test-input/labelme-subset/q2821.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, 6100538845924772892,4880316835877396793,-8528879539896295140,-4933695969863420297,3,'./data/reg-test-input/labelme-subset/q0003.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, 3479551203021573453,-3878631371961558153,4782626803258073257,6149008519092021930,100,'./data/reg-test-input/labelme-subset/q0746.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -6845870616893186872,-2484481452418414300,4574709937228232407,-1003538230961518169,100,'./data/reg-test-input/labelme-subset/q0291.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -3480718883984128294,-5727335765605246905,6316479155306461102,-6748330463045093312,100,'./data/reg-test-input/labelme-subset/q0122.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -1623500741728662685,7291709062978809194,-3119513180237368207,-600162540948284780,100,'./data/reg-test-input/exif-rotn/exif-rotn-6.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, 4237785886704974174,4165724403810072842,-5457816009823681535,-621109694718443534,100,'./data/reg-test-input/exif-rotn/exif-rotn-3.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -848408302477467180,-4163169226228512474,-3651336055051241859,3568652796583749193,100,'./data/reg-test-input/exif-rotn/exif-rotn-1.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, 7732817052992123262,-4396028573784196943,6776957633371041865,399387052429878558,100,'./data/reg-test-input/exif-rotn/exif-rotn-8.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, 985485235504397594,6008460953880507045,-1856763424508785848,7400371626640526967,100,'./data/reg-test-input/dih/bridge-6-flipy.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -506390186751121329,447837829151548400,-5517420998596354531,3739874024492931874,100,'./data/reg-test-input/dih/bridge-1-original.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -5931985745586601241,6585002181338499418,-1856744737106062153,7400286332884955528,100,'./data/reg-test-input/dih/bridge-3-rotate-180.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -6489587382679410153,-3961299772108002553,-5324561791232243716,-8663852061026373382,100,'./data/reg-test-input/dih/bridge-8-flip-minus-1.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, 3504098466769681730,-8064868805366514606,-2067699684055887191,-3272281701943220817,100,'./data/reg-test-input/dih/bridge-2-rotate-90.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -1106230730686676803,-7758848447041567859,-2067449197268194986,-3272292983748617648,100,'./data/reg-test-input/dih/bridge-7-flip-plus-1.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -6489506366711294488,-3961377498131180392,-5324480998602377213,-8664028983614222587,100,'./data/reg-test-input/dih/bridge-4-rotate-270.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, -506638251177273422,1024557701110142991,-5517243612152020510,3739760529982121181,100,'./data/reg-test-input/dih/bridge-5-flipx.jpg');
INSERT INTO hamming_test_int64 (id, hash1, hash2, hash3, hash4, quality, metadata) VALUES (NULL, 2270126048941161574,-7800014707879567459,-820918045774901498,9209293970506318329,100,'./data/reg-test-input/pen-and-coaster.png');
```
```
select * from hamming_test_int64;
+----+----------------------+----------------------+----------------------+----------------------+---------+-----------------------------------------------------+
| id | hash1                | hash2                | hash3                | hash4                | quality | metadata                                            |
+----+----------------------+----------------------+----------------------+----------------------+---------+-----------------------------------------------------+
|  1 |  2270126048941161574 | -7800014707879567459 |  -820918045774901498 |  9209293970506318329 |     100 | ./data/reg-test-input/pen-and-coaster.png           |
|  2 |  -506390186751121329 |   447837829151548400 | -5517420998596354531 |  3739874024492931874 |     100 | ./data/misc-images/b.jpg                            |
|  3 | -1851883412434831230 |  -517366565115992180 | -6982379065928243982 | -5196839458248216476 |     100 | ./data/misc-images/c.png                            |
|  4 |     1970457985089599 |    35748417275625727 |   143835907860923391 |   287953294993589247 |       0 | ./data/misc-images/small.jpg                        |
|  5 |  5232538946727641718 | -3147261139009953265 |   159701744806103262 |  -147332746629587088 |     100 | ./data/reg-test-input/labelme-subset/q1050.jpg      |
|  6 | -7409190292624597396 | -6433371965755966783 |  2156983767585631341 |   524225818483121042 |       4 | ./data/reg-test-input/labelme-subset/q0004.jpg      |
|  7 | -5669993310599220977 |  -219284899487239927 | -6523761702682218103 |  -543754086962122487 |     100 | ./data/reg-test-input/labelme-subset/q2821.jpg      |
|  8 |  6100538845924772892 |  4880316835877396793 | -8528879539896295140 | -4933695969863420297 |       3 | ./data/reg-test-input/labelme-subset/q0003.jpg      |
|  9 |  3479551203021573453 | -3878631371961558153 |  4782626803258073257 |  6149008519092021930 |     100 | ./data/reg-test-input/labelme-subset/q0746.jpg      |
| 10 | -6845870616893186872 | -2484481452418414300 |  4574709937228232407 | -1003538230961518169 |     100 | ./data/reg-test-input/labelme-subset/q0291.jpg      |
| 11 | -3480718883984128294 | -5727335765605246905 |  6316479155306461102 | -6748330463045093312 |     100 | ./data/reg-test-input/labelme-subset/q0122.jpg      |
| 12 | -1623500741728662685 |  7291709062978809194 | -3119513180237368207 |  -600162540948284780 |     100 | ./data/reg-test-input/exif-rotn/exif-rotn-6.jpg     |
| 13 |  4237785886704974174 |  4165724403810072842 | -5457816009823681535 |  -621109694718443534 |     100 | ./data/reg-test-input/exif-rotn/exif-rotn-3.jpg     |
| 14 |  -848408302477467180 | -4163169226228512474 | -3651336055051241859 |  3568652796583749193 |     100 | ./data/reg-test-input/exif-rotn/exif-rotn-1.jpg     |
| 15 |  7732817052992123262 | -4396028573784196943 |  6776957633371041865 |   399387052429878558 |     100 | ./data/reg-test-input/exif-rotn/exif-rotn-8.jpg     |
| 16 |   985485235504397594 |  6008460953880507045 | -1856763424508785848 |  7400371626640526967 |     100 | ./data/reg-test-input/dih/bridge-6-flipy.jpg        |
| 17 |  -506390186751121329 |   447837829151548400 | -5517420998596354531 |  3739874024492931874 |     100 | ./data/reg-test-input/dih/bridge-1-original.jpg     |
| 18 | -5931985745586601241 |  6585002181338499418 | -1856744737106062153 |  7400286332884955528 |     100 | ./data/reg-test-input/dih/bridge-3-rotate-180.jpg   |
| 19 | -6489587382679410153 | -3961299772108002553 | -5324561791232243716 | -8663852061026373382 |     100 | ./data/reg-test-input/dih/bridge-8-flip-minus-1.jpg |
| 20 |  3504098466769681730 | -8064868805366514606 | -2067699684055887191 | -3272281701943220817 |     100 | ./data/reg-test-input/dih/bridge-2-rotate-90.jpg    |
| 21 | -1106230730686676803 | -7758848447041567859 | -2067449197268194986 | -3272292983748617648 |     100 | ./data/reg-test-input/dih/bridge-7-flip-plus-1.jpg  |
| 22 | -6489506366711294488 | -3961377498131180392 | -5324480998602377213 | -8664028983614222587 |     100 | ./data/reg-test-input/dih/bridge-4-rotate-270.jpg   |
| 23 |  -506638251177273422 |  1024557701110142991 | -5517243612152020510 |  3739760529982121181 |     100 | ./data/reg-test-input/dih/bridge-5-flipx.jpg        |
| 24 |  2270126048941161574 | -7800014707879567459 |  -820918045774901498 |  9209293970506318329 |     100 | ./data/reg-test-input/pen-and-coaster.png           |
+----+----------------------+----------------------+----------------------+----------------------+---------+-----------------------------------------------------+

```
## Create stored function for Hamming distance on int64 4-tuple encoded hashes

```
-- This is Hamming distance, i.e. bit-count of XOR, on pairs of int64 4-tuple hashes.
-- MySQL has built-in XOR on 16-bit words via the ^ operator, and built-in bit_count.
-- Note that this function is essentially the same as the 256-bit hex-encoded function but without the string conversions.
-- So this function is simply:
-- * Bit-count of wordwise XORs (where a word is a single element of the 4-tuple);
-- * Summing those up.
DELIMITER |
CREATE FUNCTION HAMMING_DISTANCE_INT64(ha0 BIGINT(16), ha1 BIGINT(16), ha2 BIGINT(16), ha3 BIGINT(16), hb0 BIGINT(16), hb1 BIGINT(16), hb2 BIGINT(16), hb3 BIGINT(16))
  RETURNS INT
  DETERMINISTIC
  BEGIN
    DECLARE d0 INT;
    DECLARE d1 INT;
    DECLARE d2 INT;
    DECLARE d3 INT;

    SET d0 = BIT_COUNT(ha0 ^ hb0);
    SET d1 = BIT_COUNT(ha1 ^ hb1);
    SET d2 = BIT_COUNT(ha2 ^ hb2);
    SET d3 = BIT_COUNT(ha3 ^ hb3);

    RETURN d0 + d1 + d2 + d3;
    RETURN 999;
  END|
DELIMITER ;
```
```
-- The hashes used here are the int64 versions of the one used in the HAMMING_DISTANCE_256 example
SELECT HAMMING_DISTANCE_INT64(-506390195341039539, 1024298581438195696, -5517420998596346339, 3739733287004576546, -506390195341039539, 1024298581438195696, -5517420998596346339, 3739733287004576547);

+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| HAMMING_DISTANCE_INT64(-506390195341039539, 1024298581438195696, -5517420998596346339, 3739733287004576546, -506390195341039539, 1024298581438195696, -5517420998596346339, 3739733287004576547) |
+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                                                                                                1 |
+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
```

## Search for hashes
```
SELECT * FROM hamming_test_int64 WHERE HAMMING_DISTANCE_INT64(hash1, hash2, hash3, hash4, -506390186751121329, 447837829151548400, -5517420998596354531, 3739874024492931875) < 32;
+----+---------------------+--------------------+----------------------+---------------------+---------+-------------------------------------------------+
| id | hash1               | hash2              | hash3                | hash4               | quality | metadata                                        |
+----+---------------------+--------------------+----------------------+---------------------+---------+-------------------------------------------------+
|  2 | -506390186751121329 | 447837829151548400 | -5517420998596354531 | 3739874024492931874 |     100 | ./data/misc-images/b.jpg                        |
| 17 | -506390186751121329 | 447837829151548400 | -5517420998596354531 | 3739874024492931874 |     100 | ./data/reg-test-input/dih/bridge-1-original.jpg |
+----+---------------------+--------------------+----------------------+---------------------+---------+-------------------------------------------------+

SELECT * FROM hamming_test_int64 WHERE HAMMING_DISTANCE_INT64(hash1, hash2, hash3, hash4, -506390186751121329, 447837829151548400, -5517420998596354531, 3739874024492931875) < 256;
+----+----------------------+----------------------+----------------------+----------------------+---------+-----------------------------------------------------+
| id | hash1                | hash2                | hash3                | hash4                | quality | metadata                                            |
+----+----------------------+----------------------+----------------------+----------------------+---------+-----------------------------------------------------+
|  1 |  2270126048941161574 | -7800014707879567459 |  -820918045774901498 |  9209293970506318329 |     100 | ./data/reg-test-input/pen-and-coaster.png           |
|  2 |  -506390186751121329 |   447837829151548400 | -5517420998596354531 |  3739874024492931874 |     100 | ./data/misc-images/b.jpg                            |
|  3 | -1851883412434831230 |  -517366565115992180 | -6982379065928243982 | -5196839458248216476 |     100 | ./data/misc-images/c.png                            |
|  4 |     1970457985089599 |    35748417275625727 |   143835907860923391 |   287953294993589247 |       0 | ./data/misc-images/small.jpg                        |
|  5 |  5232538946727641718 | -3147261139009953265 |   159701744806103262 |  -147332746629587088 |     100 | ./data/reg-test-input/labelme-subset/q1050.jpg      |
|  6 | -7409190292624597396 | -6433371965755966783 |  2156983767585631341 |   524225818483121042 |       4 | ./data/reg-test-input/labelme-subset/q0004.jpg      |
|  7 | -5669993310599220977 |  -219284899487239927 | -6523761702682218103 |  -543754086962122487 |     100 | ./data/reg-test-input/labelme-subset/q2821.jpg      |
|  8 |  6100538845924772892 |  4880316835877396793 | -8528879539896295140 | -4933695969863420297 |       3 | ./data/reg-test-input/labelme-subset/q0003.jpg      |
|  9 |  3479551203021573453 | -3878631371961558153 |  4782626803258073257 |  6149008519092021930 |     100 | ./data/reg-test-input/labelme-subset/q0746.jpg      |
| 10 | -6845870616893186872 | -2484481452418414300 |  4574709937228232407 | -1003538230961518169 |     100 | ./data/reg-test-input/labelme-subset/q0291.jpg      |
| 11 | -3480718883984128294 | -5727335765605246905 |  6316479155306461102 | -6748330463045093312 |     100 | ./data/reg-test-input/labelme-subset/q0122.jpg      |
| 12 | -1623500741728662685 |  7291709062978809194 | -3119513180237368207 |  -600162540948284780 |     100 | ./data/reg-test-input/exif-rotn/exif-rotn-6.jpg     |
| 13 |  4237785886704974174 |  4165724403810072842 | -5457816009823681535 |  -621109694718443534 |     100 | ./data/reg-test-input/exif-rotn/exif-rotn-3.jpg     |
| 14 |  -848408302477467180 | -4163169226228512474 | -3651336055051241859 |  3568652796583749193 |     100 | ./data/reg-test-input/exif-rotn/exif-rotn-1.jpg     |
| 15 |  7732817052992123262 | -4396028573784196943 |  6776957633371041865 |   399387052429878558 |     100 | ./data/reg-test-input/exif-rotn/exif-rotn-8.jpg     |
| 16 |   985485235504397594 |  6008460953880507045 | -1856763424508785848 |  7400371626640526967 |     100 | ./data/reg-test-input/dih/bridge-6-flipy.jpg        |
| 17 |  -506390186751121329 |   447837829151548400 | -5517420998596354531 |  3739874024492931874 |     100 | ./data/reg-test-input/dih/bridge-1-original.jpg     |
| 18 | -5931985745586601241 |  6585002181338499418 | -1856744737106062153 |  7400286332884955528 |     100 | ./data/reg-test-input/dih/bridge-3-rotate-180.jpg   |
| 19 | -6489587382679410153 | -3961299772108002553 | -5324561791232243716 | -8663852061026373382 |     100 | ./data/reg-test-input/dih/bridge-8-flip-minus-1.jpg |
| 20 |  3504098466769681730 | -8064868805366514606 | -2067699684055887191 | -3272281701943220817 |     100 | ./data/reg-test-input/dih/bridge-2-rotate-90.jpg    |
| 21 | -1106230730686676803 | -7758848447041567859 | -2067449197268194986 | -3272292983748617648 |     100 | ./data/reg-test-input/dih/bridge-7-flip-plus-1.jpg  |
| 22 | -6489506366711294488 | -3961377498131180392 | -5324480998602377213 | -8664028983614222587 |     100 | ./data/reg-test-input/dih/bridge-4-rotate-270.jpg   |
| 23 |  -506638251177273422 |  1024557701110142991 | -5517243612152020510 |  3739760529982121181 |     100 | ./data/reg-test-input/dih/bridge-5-flipx.jpg        |
| 24 |  2270126048941161574 | -7800014707879567459 |  -820918045774901498 |  9209293970506318329 |     100 | ./data/reg-test-input/pen-and-coaster.png           |
+----+----------------------+----------------------+----------------------+----------------------+---------+-----------------------------------------------------+
```
