# RPC User Service

独立的用户服务仓库。它在 `user-service:50051` 提供 `GetUser` gRPC 接口，并在访问 `http://user-service:8080/demo` 时调用另一个仓库部署的 `order-service:50051`。

## Dokploy

创建 Docker Compose 服务，仓库选择本仓库，分支使用 `main`，Compose Path 填写 `./compose.yaml`。不要设置公开端口或域名。

两个仓库必须部署在同一台 Docker 主机，并加入已有的外部网络 `rpc-network`。

## 接口契约

演示阶段两个服务仓库各自保留一份相同的 `proto/rpcdemo.proto`。生产环境应把 Proto 迁移到独立的 contracts 仓库或 Schema Registry，并在 CI 中检查兼容性，避免两份接口定义发生漂移。
