-- สร้าง table users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- เพิ่ม user ตัวอย่าง
INSERT INTO users (username, password)
VALUES ('admin', '1234');