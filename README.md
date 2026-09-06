# RPC User Service

独立的用户服务仓库。它在 `user-service:50051` 提供 `GetUser` gRPC 接口，并在访问 `http://user-service:8080/demo` 时调用另一个仓库部署的 `order-service:50051`。

## Dokploy

创建 Docker Compose 服务，仓库选择本仓库，分支使用 `main`，Compose Path 填写 `./compose.yaml`。不要设置公开端口或域名。

两个仓库必须部署在同一台 Docker 主机，并加入已有的外部网络 `rpc-network`。

## 接口契约

接口的唯一源文件位于独立仓库 `Shijf/rpc-contracts`。本仓库不再保存或编译 `.proto`，只携带 `vendor/rpcdemo` 中经过验证的 Python SDK，因此 Dokploy 构建时不需要 GitHub 密钥，也不依赖外网。

当前 SDK 版本见 `vendor/RPC_CONTRACTS_VERSION`。升级协议时先在 `rpc-contracts` 生成三种语言 SDK，再执行：

```bash
/home/shijf/rpc-contracts/scripts/vendor-python.sh /home/shijf/rpc-user-service
```

检查生成代码差异、构建镜像并完成 RPC 测试后再提交。
