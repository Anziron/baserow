# Baserow WebSocket 技术架构文档

## 一、通俗理解

### 用一个生活场景来理解

想象一个微信群聊的场景:

```
┌─────────────────────────────────────────────────────────────────┐
│                        微信群 "项目组"                           │
├─────────────────────────────────────────────────────────────────┤
│  张三: 我刚更新了客户表,加了一个新客户                           │
│  [系统自动通知] 李四、王五 收到了这条消息                         │
│  李四的手机: 叮~ 显示新消息                                      │
│  王五的手机: 叮~ 显示新消息                                      │
└─────────────────────────────────────────────────────────────────┘
```

Baserow 的 WebSocket 系统就是这个"微信群"的技术实现:
- 群 = 订阅了同一个表格的所有用户
- 发消息 = 修改表格数据
- 收消息 = 其他用户的界面自动更新

### 各组件的通俗解释

| 技术组件 | 通俗比喻 | 具体作用 |
|---------|---------|---------|
| ASGI | 门卫 | 判断来的是普通访客(HTTP)还是要长期驻留的人(WebSocket) |
| JWT认证 | 身份证检查 | 验证你是谁,有没有资格进入 |
| CoreConsumer | 群管理员 | 管理谁进群、谁退群、消息怎么发 |
| PageType | 群规则 | 定义什么样的群、谁能加入、群名叫什么 |
| Django Signal | 事件触发器 | 有人改了数据,自动触发"发通知"的动作 |
| Celery队列 | 邮局 | 把通知任务排队处理,不会因为通知太多而卡住 |
| Redis Channel | 广播站 | 把消息同时发给所有在线的群成员 |

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              客户端 (浏览器)                                  │
│                    WebSocket 连接: ws://domain/ws/core/?jwt_token=xxx        │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ASGI 应用层 (asgi.py)                              │
│                    ProtocolTypeRouter 分发 HTTP/WebSocket                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        ┌───────────────────┐                   ┌───────────────────┐
        │   HTTP 请求处理    │                   │  WebSocket 处理   │
        │   (Django Views)  │                   │  (Channels)       │
        └───────────────────┘                   └───────────────────┘
                    │                                       │
                    ▼                                       ▼
        ┌───────────────────┐                   ┌───────────────────┐
        │   业务 Handler    │                   │   CoreConsumer    │
        │   (RowHandler等)  │                   │   (消费者)         │
        └───────────────────┘                   └───────────────────┘
                    │                                       │
                    ▼                                       ▼
        ┌───────────────────┐                   ┌───────────────────┐
        │   Django Signal   │ ──────────────▶   │   Channel Layer   │
        │   (信号系统)       │                   │   (Redis)         │
        └───────────────────┘                   └───────────────────┘
                    │
                    ▼
        ┌───────────────────┐
        │   Celery Task     │
        │   (异步任务队列)   │
        └───────────────────┘
```

## 三、核心组件

### 1. ASGI 应用入口

文件位置: `backend/src/baserow/config/asgi.py`

```python
application = ProtocolTypeRouter({
    "http": ConcurrencyLimiterASGI(...),  # HTTP 请求走 Django
    "websocket": websocket_router,         # WebSocket 请求走 Channels
})
```

### 2. JWT 认证中间件

文件位置: `backend/src/baserow/ws/auth.py`

```python
class JWTTokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # 从 URL 参数获取 JWT token
        get = parse_qs(scope["query_string"].decode("utf8"))
        jwt_token = get.get("jwt_token")
        
        if jwt_token:
            scope["user"] = await get_user(jwt_token[0])
            scope["web_socket_id"] = str(uuid.uuid4())
```

### 3. 核心消费者 (CoreConsumer)

文件位置: `backend/src/baserow/ws/consumers.py`

主要功能:
- 管理 WebSocket 连接的建立和断开
- 处理客户端发送的订阅/取消订阅请求
- 接收频道层广播的消息并转发给客户端

### 4. 页面类型注册系统

文件位置: `backend/src/baserow/ws/registries.py`

已注册的页面类型:
- `TablePageType`: 表格页面
- `RowPageType`: 行详情页面
- `PublicViewPageType`: 公共视图页面

### 5. Celery 异步任务

文件位置: `backend/src/baserow/ws/tasks.py`

```python
@app.task(bind=True)
def broadcast_to_channel_group(self, channel_group_name, payload, 
                               ignore_web_socket_id=None, exclude_user_ids=None):
    """广播消息到指定频道组"""
```

## 四、数据流程

### 数据变更广播流程

```
用户A (HTTP)              服务端                    用户B (WebSocket)
  │                         │                              │
  │ ── POST 创建行 ────────▶│                              │
  │                         │ RowHandler.create_row()      │
  │                         │ 数据保存到数据库              │
  │                         │ 触发 rows_created 信号       │
  │ ◀── HTTP 响应 ─────────│                              │
  │                         │ 事务提交,执行 on_commit      │
  │                         │ Celery Worker 处理任务       │
  │                         │ ─── WebSocket 消息 ─────────▶│
  │                         │    {"type": "rows_created"}  │
```

## 五、常见问题

### Q1: 队列是用来发消息的吗?

不是。队列(Celery)的作用是把"通知在线用户"这个任务异步处理,不会调用任何外部HTTP接口。

### Q2: WebSocket 断开后会丢消息吗?

会。WebSocket 是实时通信,不保证消息持久化。断开期间的消息不会补发,重连后需要重新订阅页面。

## 六、技术栈总结

| 组件 | 技术 | 作用 |
|------|------|------|
| ASGI 服务器 | Uvicorn/Daphne | 处理异步请求 |
| WebSocket 框架 | Django Channels | WebSocket 连接管理 |
| 消息队列 | Celery + Redis | 异步任务处理 |
| 频道层 | channels_redis | 跨进程消息传递 |
| 认证 | JWT | 用户身份验证 |
