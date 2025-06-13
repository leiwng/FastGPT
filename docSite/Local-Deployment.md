# 开发环境本地部署的补充说明

## git repo
https://github.com/leiwng/FastGPT.git

## 部署位置
host: 106.75.23.69

path: /data/leiw/prj/FastGPT

## 原版参考本地部署文档
https://doc.tryfastgpt.ai/docs/development/intro/

 - 前置依赖项，需满足，尤其是Node.js的版本要求v20.18.0
 - 安装数据库和其他支撑服务的部署，参考接下来的章节。
 - 环境变量和配置文件，参考接下来的章节。
 - 安装依赖。
   ```bash
    cd /data/leiw/prj/FastGPT
    pnpm i
   ```
 - 启动服务：
   ```bash
    cd /data/leiw/prj/FastGPT/projects/app
    pnpm dev:23023
   ```

## 支持服务

### 支持服务容器配置目录
./common_services

### Redis & Postgres
./docker-compose-redis-postgres.yaml

sudo docker compose -f docker-compose-redis-postgres.yaml up -d

### MongoDB & HAproxy
./haproxy.cfg

./docker-compose-mongodb.yaml

sudo docker compose -f docker-compose-mongodb.yaml up -d

## 配置文件
./projects/app/.env.local
修改参数：
 - OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
 - CHAT_API_KEY=sk-6ec62194ca464ba5a6011c70889e8210
 - REDIS_URL=redis://127.0.0.1:26379
 - MONGODB_URI=mongodb://root:Welcome1@127.0.0.1:29019/fastgpt?authSource=admin&replicaSet=rs0&directConnection=true
 - MONGODB_LOG_URI=mongodb://root:Welcome1@127.0.0.1:29019/fastgpt?authSource=admin&replicaSet=rs0&directConnection=true
 - PG_URL=postgresql://postgres:postgres@127.0.0.1:25433/postgres
 - FE_DOMAIN==http://106.75.23.69:2024/fastgpt
 - FILE_DOMAIN=http://106.75.23.69:2024/fastgpt
 - NEXT_PUBLIC_BASE_URL=/fastgpt
 - CHAT_LOG_URL=http://localhost:28080

./projects/app/next.config.js
修改代码：
 ```javascript
   ... // 其他配置保持不变
   basePath: process.env.NEXT_PUBLIC_BASE_URL || '',
   assetPrefix: process.env.NEXT_PUBLIC_BASE_URL || '',
   ... // 其他配置保持不变
 ```
./projects/app/data/config.local.json
将 config.json 复制一份为 config.local.json，未作修改。

./projects/app/data/package.json
修改代码：
```json
  "scripts": {
    ... // 其他脚本保持不变
    "dev:23023": "next dev -p 23023",
    ... // 其他脚本保持不变
  },
```

## Nginx 配置与服务
  通过医小助的Nginx服务来代理访问FastGPT的前端服务。

### Nginx 配置文件
  /data/zzl/deploy/conf.d/default.conf

### Nginx 相关命令

#### 测试配置文件语法是否正确
  sudo docker exec deploy-langgraph-nginx-1 nginx -t

#### 重新加载配置
  sudo docker exec deploy-langgraph-nginx-1 nginx -s reload

## 安装依赖。
   ```bash
     cd /data/leiw/prj/FastGPT
     pnpm i
   ```

## 启动服务
   ```bash
     cd /data/leiw/prj/FastGPT/projects/app
     pnpm dev:23023
     或
     nohup pnpm dev:23023 > fastgpt_<YYYY-MM-DD_MM-SS>.log 2>&1 &
     ps aux | grep "next\|node" | grep 23023
     tail -f fastgpt_<YYYY-MM-DD_MM-SS>.log
   ```
