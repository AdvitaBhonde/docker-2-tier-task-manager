-- Initial database schema for 2-Tier Task Manager Application

CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM('pending', 'completed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed starter data for initial demonstration
INSERT INTO tasks (title, description, status) VALUES
('Set up Docker Compose', 'Configure multi-container setup with MySQL, Flask backend, and Nginx frontend.', 'completed'),
('Deploy on AWS EC2', 'Launch an Ubuntu EC2 instance, configure Security Groups, and deploy containerized app.', 'pending'),
('Prepare DevOps Portfolio', 'Document architecture, API endpoints, and Docker workflow in GitHub README.', 'pending');
