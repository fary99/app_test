# M20 应用商店种子目录（原型）

推送到公开仓库 [fary99/app_test](https://github.com/fary99/app_test) 后，板上商店 App 读取：

`https://raw.githubusercontent.com/fary99/app_test/main/catalog.json`

## 布局

```text
catalog.json
apps/<id>/          源工程
packages/<id>-<ver>.zip
```

## 重新打包

```bash
./pack.sh
# 或改 raw 基址：
STORE_BASE=https://raw.githubusercontent.com/fary99/app_test/main ./pack.sh
```

将本目录内容（含 `catalog.json`、`apps/`、`packages/`）推到该仓库的 `main` 分支即可。
