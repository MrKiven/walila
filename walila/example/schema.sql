DROP TABLE IF EXISTS todo;

CREATE TABLE IF NOT EXISTS todo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(20) DEFAULT "",
    is_done INT(1) DEFAULT 0,
    KEY `idx_key` (`id`, `title`)
);
