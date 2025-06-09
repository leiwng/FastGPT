#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB 副本集连接测试脚本
用于验证 MongoDB 副本集服务是否正常工作
"""

import pymongo
import time
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure

def test_mongodb_connection():
    """测试 MongoDB 副本集连接"""

    # 配置连接参数
    configs = [
        {
            "name": "直接连接主节点 (29019)",
            "uri": "mongodb://root:Welcome1@127.0.0.1:29019/fastgpt?authSource=admin&replicaSet=rs0&directConnection=true"
        },
        {
            "name": "副本集连接 (29019)",
            "uri": "mongodb://root:Welcome1@127.0.0.1:29019/fastgpt?authSource=admin&replicaSet=rs0"
        },
        {
            "name": "通过 HAProxy 连接 (28018)",
            "uri": "mongodb://root:Welcome1@127.0.0.1:28018/fastgpt?authSource=admin&replicaSet=rs0"
        },
        {
            "name": "完整副本集连接",
            "uri": "mongodb://root:Welcome1@fg-mongo1:27017,fg-mongo2:27017,fg-mongo3:27017/fastgpt?authSource=admin&replicaSet=rs0&readPreference=primary"
        }
    ]

    print("=" * 80)
    print("MongoDB 副本集连接测试")
    print("=" * 80)

    for config in configs:
        print(f"\n📡 测试: {config['name']}")
        print(f"🔗 连接字符串: {config['uri']}")
        print("-" * 60)

        try:
            # 创建客户端连接
            client = MongoClient(
                config['uri'],
                serverSelectionTimeoutMS=5000,  # 5秒超时
                connectTimeoutMS=5000,
                maxPoolSize=10
            )

            # 测试连接
            print("⏳ 正在连接...")
            start_time = time.time()

            # 执行 ping 命令
            result = client.admin.command('ping')
            connect_time = time.time() - start_time

            print(f"✅ 连接成功! 耗时: {connect_time:.3f}s")
            print(f"📊 Ping 结果: {result}")

            # 获取副本集状态
            try:
                rs_status = client.admin.command('replSetGetStatus')
                print(f"🔄 副本集名称: {rs_status.get('set', 'N/A')}")
                print(f"📍 当前节点状态: {rs_status.get('myState', 'N/A')}")

                # 显示所有成员状态
                members = rs_status.get('members', [])
                print(f"👥 副本集成员数量: {len(members)}")

                for member in members:
                    state_str = member.get('stateStr', 'UNKNOWN')
                    name = member.get('name', 'N/A')
                    health = member.get('health', 0)
                    print(f"   - {name}: {state_str} (健康度: {health})")

            except OperationFailure as e:
                print(f"⚠️  无法获取副本集状态: {e}")

            # 测试数据库操作
            try:
                # 列出数据库
                db_list = client.list_database_names()
                print(f"💾 可访问的数据库: {db_list}")

                # 测试写入操作
                test_db = client.test_connection
                test_collection = test_db.test_collection

                # 插入测试文档
                test_doc = {
                    "test_time": time.time(),
                    "message": "MongoDB 连接测试",
                    "config": config['name']
                }

                insert_result = test_collection.insert_one(test_doc)
                print(f"✏️  测试写入成功, ID: {insert_result.inserted_id}")

                # 读取测试文档
                found_doc = test_collection.find_one({"_id": insert_result.inserted_id})
                if found_doc:
                    print(f"📖 测试读取成功: {found_doc['message']}")

                # 删除测试文档
                delete_result = test_collection.delete_one({"_id": insert_result.inserted_id})
                print(f"🗑️  测试删除成功, 删除数量: {delete_result.deleted_count}")

            except Exception as e:
                print(f"❌ 数据库操作测试失败: {e}")

            # 获取服务器信息
            try:
                server_info = client.server_info()
                print(f"🖥️  MongoDB 版本: {server_info.get('version', 'N/A')}")
                print(f"🏠 服务器地址: {client.address}")
            except Exception as e:
                print(f"⚠️  无法获取服务器信息: {e}")

            print("✅ 所有测试通过!")

        except ServerSelectionTimeoutError as e:
            print(f"❌ 服务器选择超时: {e}")
            print("💡 可能的原因:")
            print("   - MongoDB 服务未启动")
            print("   - 网络连接问题")
            print("   - 副本集配置错误")

        except ConnectionFailure as e:
            print(f"❌ 连接失败: {e}")
            print("💡 可能的原因:")
            print("   - 认证失败")
            print("   - 端口未开放")
            print("   - 防火墙阻止")

        except OperationFailure as e:
            print(f"❌ 操作失败: {e}")
            print("💡 可能的原因:")
            print("   - 权限不足")
            print("   - 数据库配置问题")

        except Exception as e:
            print(f"❌ 未知错误: {e}")

        finally:
            try:
                client.close()
                print("🔌 连接已关闭")
            except:
                pass

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

def test_individual_nodes():
    """测试各个 MongoDB 节点的连接"""

    nodes = [
        {"name": "fg-mongo1", "port": 29019},
        {"name": "fg-mongo2", "host": "fg-mongo2", "port": 27017},
        {"name": "fg-mongo3", "host": "fg-mongo3", "port": 27017}
    ]

    print("\n" + "=" * 80)
    print("单节点连接测试")
    print("=" * 80)

    for node in nodes:
        host = node.get("host", "127.0.0.1")
        port = node["port"]
        name = node["name"]

        uri = f"mongodb://root:Welcome1@{host}:{port}/admin?authSource=admin"

        print(f"\n🔍 测试节点: {name} ({host}:{port})")
        print("-" * 40)

        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            result = client.admin.command('ping')
            server_info = client.server_info()

            print(f"✅ {name} 连接成功")
            print(f"📊 版本: {server_info.get('version', 'N/A')}")

            # 尝试获取副本集状态
            try:
                rs_status = client.admin.command('replSetGetStatus')
                state = next((m['stateStr'] for m in rs_status['members'] if m.get('self')), 'UNKNOWN')
                print(f"🔄 副本集状态: {state}")
            except:
                print("⚠️  无法获取副本集状态")

        except Exception as e:
            print(f"❌ {name} 连接失败: {e}")

        finally:
            try:
                client.close()
            except:
                pass

if __name__ == "__main__":
    # 检查是否安装了 pymongo
    try:
        import pymongo
        print(f"📦 PyMongo 版本: {pymongo.version}")
    except ImportError:
        print("❌ 请先安装 pymongo: pip install pymongo")
        sys.exit(1)

    # 运行测试
    test_mongodb_connection()
    test_individual_nodes()