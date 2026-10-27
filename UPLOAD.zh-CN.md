# 完整上传步骤

当前交付没有修改参考作者的仓库。连接到 Codex 的 GitHub 账号读取为 `qyf2`；
本次连接没有“创建仓库”工具，且未返回可写目标仓库，本机也没有已安装的 GitHub CLI。
因此采用用户允许的手动上传交付方式，无需把密码或 token 发到聊天中。

## 方法一：GitHub 网页上传

1. 将交付的 `codex-mv-skill.zip` 解压。进入里面的 `codex-mv-skill` 文件夹，应直接看到
   `README.md`、`LICENSE`、`skills`、`scripts`、`tests` 等内容。
2. 在浏览器登录你要发布的 GitHub 账号。当前连接账号是 `qyf2`，如果你使用另一账号，以浏览器登录账号为准。
3. 打开 [新建仓库页面](https://github.com/new)，Owner 选你的个人账号，仓库名填 `codex-mv-skill`。
   描述可填：`Codex skill for hand-painted music videos with LRC karaoke, beat analysis and reliable rendering`。
4. 根据分享需要选 Public 或 Private。**先不要勾选**初始化 README、.gitignore 或 License，点击 Create repository。
5. 在空仓库页点击 `uploading an existing file`；或进入仓库后 `Add file` → `Upload files`。
6. 拖入第 1 步文件夹**里面的文件和目录**，不要多套一层 `codex-mv-skill/`，也不要只上传 ZIP。
   确认 `skills/song-mv/assets/template/src/core.js`、`clawd.js`、`package-lock.json` 等都保留原路径。
   隐藏的 `.gitignore`、`.gitattributes` 也应上传；Windows 资源管理器可开启“显示隐藏的项目”。
7. Commit message 填 `Add complete Codex song MV skill`，提交到 `main`。
8. 打开 `https://github.com/你的用户名/codex-mv-skill`，确认首页显示 README；
   打开 `skills/song-mv/SKILL.md`，确认 YAML frontmatter、脚本和模板文件都在。
9. 如希望出现在个人主页，打开 GitHub 个人主页 → `Customize your pins` → 勾选该仓库。

GitHub 网页目前支持单次最多 100 文件、每个文件最多 25 MiB；本交付排除了 npm 依赖和帧缓存。
如果网页上传遗漏隐藏文件或目录，使用下面的 Git 方法。

## 方法二：Git 命令（推荐，完整保留目录和隐藏文件）

先完成上面第 3–4 步创建空仓库，并安装 [Git](https://git-scm.com/downloads)。
PowerShell 中进入解压后的仓库根目录，执行：

```powershell
Set-Location -LiteralPath "D:\下载目录\codex-mv-skill"
git init
git branch -M main
git add .
git diff --cached --stat
git commit -m "Add complete Codex song MV skill"
git remote add origin https://github.com/你的用户名/codex-mv-skill.git
git push -u origin main
```

将路径和 `你的用户名` 换为实际值。如果发布到当前连接账号，remote 为：
`https://github.com/qyf2/codex-mv-skill.git`。
首次提交提示缺少姓名/邮箱时，只在此仓库设置，然后重试 commit：

```powershell
git config user.name "你的 GitHub 用户名"
git config user.email "GitHub 设置中显示的提交邮箱或 noreply 邮箱"
```

推送时按 Git Credential Manager 的浏览器登录流程授权。GitHub 不接受账户密码作为 HTTPS Git 密码。
已有 origin 时先 `git remote -v` 核对；不要不经检查就覆盖其他仓库地址。
如果远端已经初始化 README，用新目录 `git clone` 该仓库，再把交付内容复制进去、commit/push；不需要强制推送。

## 上传后使用

可以把以下提示发给 Codex：

```text
使用 $skill-installer，从 https://github.com/你的用户名/codex-mv-skill
安装 skills/song-mv，然后用 $song-mv 制作我提供歌曲的 MV。
```

也可克隆后用本仓库的安装器，清楚选择项目或用户目录：

```powershell
git clone https://github.com/你的用户名/codex-mv-skill.git
Set-Location -LiteralPath codex-mv-skill
python scripts/install.py --dest "D:\我的MV项目\.agents\skills"
```

参考：[新建 GitHub 仓库](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)、
[上传文件](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)、
[Codex skill 目录](https://learn.chatgpt.com/docs/build-skills)。
