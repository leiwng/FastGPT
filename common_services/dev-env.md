您提出了一个很好的问题。让我们解决端口冲突问题，同时保持高可用性。以下是优化后的解决方案：

## 高可用 MongoDB 副本集连接解决方案（避开27017端口）

在您的当前配置中，您使用了 HAProxy 来实现 MongoDB 副本集的负载均衡，但由于宿主机上的 27017 端口已被占用，导致无法正常访问 MongoDB 服务。我们将通过以下步骤解决这个问题：
1. **使用 HAProxy 监听新的端口**：将 HAProxy 的端口映射到宿主机的一个未被占用的端口（例如 27018）。
2. **更新应用程序连接字符串**：确保应用程序连接到新的端口。
3. **验证高可用性**：确保即使某个 MongoDB 节点挂掉，服务仍然可用。
以下是更新后的 `docker-compose.yml` 文件和 HAProxy 配置文件：

```yaml
version: '3.8'

services:
  mongo1:
    image: mongo:6.0
    container_name: mongo1
    command: mongod --replSet rs0 --bind_ip_all
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: example
    volumes:
      - mongo1-data:/data/db
    networks:
      - mongo-net

  mongo2:
    image: mongo:6.0
    container_name: mongo2
    command: mongod --replSet rs0 --bind_ip_all
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: example
    volumes:
      - mongo2-data:/data/db
    networks:
      - mongo-net

  mongo3:
    image: mongo:6.0
    container_name: mongo3
    command: mongod --replSet rs0 --bind_ip_all
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: example
    volumes:
      - mongo3-data:/data/db
    networks:
      - mongo-net

  mongo-init:
    image: mongo:6.0
    container_name: mongo-init
    depends_on:
      - mongo1
      - mongo2
      - mongo3
    command: >
      bash -c "until mongosh --host mongo1 --username root --password example --eval 'db.runCommand({ ping: 1 })' > /dev/null 2>&1; do
        echo 'Waiting for MongoDB...';
        sleep 5;
      done;
      echo 'Initializing replica set...';
      mongosh --host mongo1 --username root --password example --eval 'rs.initiate({
        _id: \"rs0\",
        members: [
          {_id: 0, host: \"mongo1:27017\"},
          {_id: 1, host: \"mongo2:27017\"},
          {_id: 2, host: \"mongo3:27017\"}
        ]
      })';
      echo 'Replica set initialized!'"
    networks:
      - mongo-net

  # HAProxy负载均衡器 - 使用新端口
  haproxy:
    image: haproxy:2.6
    container_name: haproxy-mongo
    ports:
      - "27018:27017"  # 使用新端口27018
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg
    networks:
      - mongo-net
    depends_on:
      - mongo1
      - mongo2
      - mongo3
    restart: unless-stopped

networks:
  mongo-net:
    driver: bridge

volumes:
  mongo1-data:
  mongo2-data:
  mongo3-data:
```

## HAProxy配置文件 (haproxy.cfg)

```cfg
global
    daemon
    maxconn 256

defaults
    mode tcp
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

listen mongo
    bind *:27017  # HAProxy容器内部监听端口
    mode tcp
    balance leastconn
    option tcp-check
    tcp-check expect string ismaster
    server mongo1 mongo1:27017 check
    server mongo2 mongo2:27017 check
    server mongo3 mongo3:27017 check
```

## 关键优化点

1. **端口映射调整**：
   ```yaml
   ports:
     - "27018:27017"  # 使用新端口27018
   ```
   - HAProxy容器将宿主机的27018端口映射到容器内部的27017端口
   - 完全避开宿主机上已被占用的27017端口

2. **连接字符串更新**：
   应用程序使用新端口连接：
   ```
   mongodb://root:example@localhost:27018/?replicaSet=rs0
   ```

3. **内部端口保持不变**：
   - MongoDB节点间仍使用27017端口通信
   - HAProxy内部监听27017端口（容器内部）

## 高可用性验证

即使mongo1挂掉，服务仍然可用：

1. **模拟主节点故障**：
   ```bash
   docker stop mongo1
   ```

2. **检查新主节点**：
   ```bash
   docker exec -it mongo2 mongosh -u root -p example --eval "rs.status()"
   ```

3. **测试连接**：
   ```bash
   mongosh "mongodb://root:example@localhost:27018/?replicaSet=rs0" --eval "db.runCommand({ping:1})"
   ```
   应该返回：
   ```json
   { "ok" : 1 }
   ```

## 备选方案：使用随机端口

如果不确定哪个端口可用，可以让Docker自动分配：

```yaml
haproxy:
  ports:
    - "27017"  # Docker将随机分配主机端口
```

然后查看实际映射的端口：
```bash
docker port haproxy-mongo 27017
```

## 端口冲突解决建议

1. **查找占用27017端口的进程**：
   ```bash
   # Linux/MacOS
   sudo lsof -i :27017

   # Windows
   netstat -ano | findstr ":27017"
   ```

2. **释放端口**：
   - 停止占用进程
   - 或修改现有服务的端口配置

3. **使用不同IP绑定**：
   ```yaml
   ports:
     - "127.0.0.1:27018:27017"  # 仅本地访问
   ```

## 完整部署流程

1. 创建项目目录：
   ```bash
   mkdir mongo-replica && cd mongo-replica
   ```

2. 创建docker-compose.yml：
   ```bash
   nano docker-compose.yml
   ```
   粘贴上面的YAML配置

3. 创建haproxy.cfg：
   ```bash
   nano haproxy.cfg
   ```
   粘贴上面的HAProxy配置

4. 启动集群：
   ```bash
   docker compose up -d
   ```

5. 验证部署：
   ```bash
   # 检查副本集状态
   docker exec -it haproxy-mongo bash -c "echo 'rs.status()' | mongosh 'mongodb://root:example@localhost:27017/?replicaSet=rs0'"

   # 测试连接
   mongosh "mongodb://root:example@localhost:27018/?replicaSet=rs0"
   ```

这个解决方案既避开了宿主机上的27017端口冲突，又通过HAProxy实现了真正的高可用性，确保即使某个节点故障，服务仍然可以通过27018端口正常访问。