#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1

# 默认值
DATA_DIR="data"
USER_NAME="Yumetest.json"
MC_ARGS=()
MP_ARGS=()

DATA_SET=false
MC_SET=false
MP_SET=false
USER_SET=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--data)
            DATA_DIR="$2"; DATA_SET=true; shift 2 ;;
        -mc|--mandatory_characters)
            MC_ARGS=("${@:2:10}"); MC_SET=true; shift 11 ;;
        -mp|--mandatory_posters)
            MP_ARGS=("${@:2:10}"); MP_SET=true; shift 11 ;;
        -h|--help)
            python -m src.ActorFormation --help; exit 0 ;;
        *)
            echo "未知选项: $1"; exit 1 ;;
    esac
done

CMD=(python -m src.ActorFormation "$USER_NAME")
$DATA_SET && CMD+=(-d "$DATA_DIR")
$MC_SET && CMD+=(-mc "${MC_ARGS[@]}")
$MP_SET && CMD+=(-mp "${MP_ARGS[@]}")

echo "Running: ${CMD[*]}"

trap '' INT

"${CMD[@]}"

trap - INT

read -r -n 1 -p "按任意键退出..."