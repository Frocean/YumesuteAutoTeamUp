#!/bin/bash
# 构建配队状态, 并将结果自动上传至服务器并接收返回的结果. 服务器那边暂时鸽掉了.
# DATA_DIR 为存储游戏内的 json 文件地址
# USER_DATA_PATH 为用户游戏数据的 JSON 文件，将通过 stdin 传入 Python
# MANDATORY_CHARS 为角色输入. 每两个选项为一组, 第一个是必上场的角色 ID, 随后是其必须站的位置. 五组输入之间无需顾虑顺序.
# MANDATORY_POSTERS 为海报输入, 与上面相同.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1

# 默认值
DATA_DIR="data"
USER_DATA_PATH="${PROJECT_ROOT}/test.json"

DATA_SET=false
MC_SET=false
MP_SET=false
USER_SET=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--data)
            DATA_DIR="$2"
            DATA_SET=true
            shift 2
            ;;
        -mc|--mandatory_characters)
            MANDATORY_CHARS=("${@:2:10}")
            MC_SET=true
            shift 11
            ;;
        -mp|--mandatory_posters)
            MANDATORY_POSTERS=("${@:2:10}")
            MP_SET=true
            shift 11
            ;;
        -u|--user)
            USER_DATA_PATH="$2"
            USER_SET=true
            shift 2
            ;;
        -h|--help)
            python StartForServer.py --help
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            exit 1
            ;;
    esac
done

ARGS=()
$DATA_SET && ARGS+=(-d "$DATA_DIR")
$MC_SET && ARGS+=(-mc "${MANDATORY_CHARS[@]}")
$MP_SET && ARGS+=(-mp "${MANDATORY_POSTERS[@]}")

CMD_STR="python Start.py"
[ ${#ARGS[@]} -gt 0 ] && CMD_STR+=" ${ARGS[*]}"
if [ -n "$USER_DATA_PATH" ]; then
    CMD_STR+=" < \"$USER_DATA_PATH\""
fi
echo "正在运行: $CMD_STR"

if [ -n "$USER_DATA_PATH" ]; then
    if [ ! -f "$USER_DATA_PATH" ]; then
        echo "用户数据文件 '$USER_DATA_PATH' 不存在"
        exit 1
    fi
    python Start.py "${ARGS[@]}" < "$USER_DATA_PATH"
else
    python Start.py "${ARGS[@]}"
fi

read -r -p "按回车键退出..."