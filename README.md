# same-same

离线找出目录里的重复文件，按文件大小和 SHA-256 内容摘要筛选。工具只读取文件，不会删除、移动或改写任何东西。

## 使用

需要 Python 3.8+，不安装依赖。

~~~sh
python same_same.py ~/Pictures ~/Downloads
~~~

也可以只检查一个文件：

~~~sh
python same_same.py ./archive-copy.zip
~~~

PowerShell 示例：

~~~powershell
py .\same_same.py "$HOME\Pictures" "$HOME\Downloads"
~~~

扫描目录时会包含隐藏文件，跳过符号链接和目录联接。相同大小的文件才会读取并计算摘要；读取失败会报告并以非零状态退出。结果会显示本地路径，但不会显示文件内容。不可打印字符会转义显示。输出中的每一组都需要你自己检查，工具不会替你删除文件。
硬链接的多个路径也会被列出，因此结果不等于可回收空间估算。

## 许可

MIT，见 [LICENSE](LICENSE)。
## Linux x86_64 下载

- [单文件版](https://github.com/506058115-cmd/same-same/releases/download/v1.0.0/same-same-linux-x86_64-onefile.tar.gz)
- [目录版](https://github.com/506058115-cmd/same-same/releases/download/v1.0.0/same-same-linux-x86_64-onedir.tar.gz)
- [v1.0.0 Release 页面](https://github.com/506058115-cmd/same-same/releases/tag/v1.0.0)

压缩包附带构建信息和依赖许可证；Release 另附 SHA-256 校验文件。产物在 WSL Ubuntu 24.04（Python 3.12.3、PyInstaller 6.22.2）中构建，目标为 GNU/Linux x86_64。较旧的发行版可能需要兼容的 glibc。
