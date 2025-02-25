-- 成就进度相关表
# CREATE TABLE my_achievements (
#     achievement_name VARCHAR(50) PRIMARY KEY COMMENT '成就名称',
#     current_value INT DEFAULT 0,
#     unlock_status ENUM('locked','unlocked') DEFAULT 'locked',
#     last_updated DATE
# ) COMMENT='示例数据：
# ("代码百人斩", 87, "unlocked", "2025-02-22")
# ("早睡达人", 15, "locked", NULL)';

-- 成就定义表
CREATE TABLE achievements
(
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    title              VARCHAR(100) NOT NULL COMMENT '成就名称',
    description        TEXT         NOT NULL COMMENT '详细描述',
    tier               TINYINT                                       DEFAULT 1 COMMENT '成就级别（1: Bronze, 2: Silver, 3: Gold, 4: Platinum)',
    progress_degree    DECIMAL                                       DEFAULT 0 COMMENT '进度度量标准（例如：提交的代码数量）',
    badge_type         ENUM ('bronze', 'silver', 'gold', 'platinum') DEFAULT 'bronze' COMMENT '对应 badges 的类型',
    hidden             BOOLEAN                                       DEFAULT FALSE COMMENT '是否隐藏（用于内部测试或特殊用途）',
    parent_achievement INT,
    FOREIGN KEY (parent_achievement) REFERENCES achievements (id) ON UPDATE CASCADE ON DELETE SET NULL,
    unlock_condition   JSON COMMENT '解锁该成就的条件（JSON格式）',
    progress_metric    VARCHAR(200)                                  DEFAULT '0' COMMENT '进度度量的详细信息（例如：百分比）',
    source_type        INT                                           DEFAULT 0 COMMENT '数据源 ID（外键）'
);

drop table achievements;

-- 用户成就表
CREATE TABLE user_achievements
(
    user_id               INT NOT NULL,
    achievement_id        INT NOT NULL,
    achievement_record_id INT      DEFAULT 0 COMMENT '与该成就相关的记录 ID',
    locked_at             DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '解锁时间',
    last_updated          DATE COMMENT '成就升级',
    FOREIGN KEY (achievement_id) REFERENCES achievements (id)
);

drop table user_achievements;

# -- 合并计划和实际时间
# CREATE TABLE time_plans
# (
#     plan_date     DATE PRIMARY KEY,
#     planned_total INT COMMENT '当日计划总分钟数',
#     actual_total  INT COMMENT '实际执行总分钟数',
#     focus_ratio   DECIMAL(4, 2) COMMENT '专注比例',
#     CHECK (planned_total <= 1440)
# ) COMMENT ='示例：
# ("2025-02-23", 480, 420, 0.72)';

-- 计划表（根据toggl的goal作为计划，由哪些Project）
CREATE TABLE personal_plans
(
    plan_id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT            NOT NULL,
    plan_name           VARCHAR(30)    NOT NULL COMMENT '计划名',
    plan_type           tinyint        not null comment '计划类型 1-coding技能，2-健身计划，3-',
    reference_project   int comment '根据计划类型，计划关联项目',
    daily_plan_duration DECIMAL(10, 2) NOT NULL comment '计划每天投入时长',
    tag_list            JSON           NOT NULL,
    project_list        JSON           NOT NULL,
    create_time         DATETIME       NOT NULL,
    update_time         DATETIME       NOT NULL COMMENT '更新时间',
    deadline            DATE           NOT NULL COMMENT '截止时间'
) ENGINE = InnoDB;

drop TABLE personal_plans;

-- toggl的数据表
CREATE TABLE toggl_datas
(
    id                INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT         NOT NULL,
    toggl_accounts_id VARCHAR(30) NOT NULL,
    clients           JSON        NOT NULL,
    time_entries      JSON        NOT NULL,
    workspace_list    JSON        NOT NULL comment 'workspaces',
    tag_list          JSON        NOT NULL,
    project_list      JSON        NOT NULL,
    create_time       DATETIME    NOT NULL,
    update_time       DATETIME    NOT NULL COMMENT '更新时间'
) ENGINE = InnoDB;

drop TABLE toggl_datas;

-- 用户Github数据表
CREATE TABLE github_events
(
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    local_user_id  INT          NOT NULL COMMENT '关联本地用户系统ID',
    github_user_id BIGINT       NOT NULL COMMENT 'GitHub用户数字ID',
    event_type     VARCHAR(30)  NOT NULL COMMENT '事件类型（见附录）',
    repo_id        BIGINT       NOT NULL COMMENT '仓库数字ID',
    repo_name      VARCHAR(255) NOT NULL COMMENT 'owner/repo格式',
    repo_url       VARCHAR(512) NOT NULL COMMENT '仓库HTTPS地址',
    event_time     DATETIME(3)  NOT NULL COMMENT '事件触发时间（含毫秒）',
    event_date     DATE GENERATED ALWAYS AS (DATE(event_time)) STORED COMMENT '生成日期分区字段',

    -- 通用指标字段
    commit_count   SMALLINT UNSIGNED DEFAULT 0 COMMENT '提交次数（仅PushEvent有效）',
    code_changes   JSON COMMENT '代码变更统计，例：
        {
            "additions": 120,
            "deletions": 45,
            "files": ["src/main.py", "docs/README.md"]
        }',

    -- 事件专用存储
    event_specific JSON COMMENT '事件特有数据，结构示例：
        {
            "PullRequest": {
                "action": "closed",
                "number": 128,
                "state": "merged",
                "comments": 5
            },
            "Issue": {
                "number": 89,
                "title": "Bug fix"
            }
        }',

    INDEX idx_user_activity (local_user_id, event_date),
    INDEX idx_event_analysis (event_type, repo_id, event_date),
    INDEX idx_time_series (event_time)
) ENGINE = InnoDB
    COMMENT ='GitHub事件核心存储表';


-- 简化Anki记录
CREATE TABLE anki_logs
(
    card_id      VARCHAR(20),
    review_date  DATE,
    memory_level TINYINT COMMENT '1-5记忆强度',
    PRIMARY KEY (card_id, review_date)
) COMMENT ='示例：
("算法-二叉树", "2025-02-23", 4)';