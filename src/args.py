import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='Yumesute auto team-up')
    parser.add_argument('user', nargs='?', metavar='File name for user data', default='Yumetest.json', help='账号数据名称')
    parser.add_argument('-d', '--data', metavar='DIR for game data', default='data', help='游戏内资源路径')
    parser.add_argument('-mc', '--mandatory_characters', type=int, nargs=10, default=[0]*10,
                        help='交替输入必选角色及其固定位置, 不选则填0, 以空格分割')
    parser.add_argument('-mp', '--mandatory_posters', type=int, nargs=10, default=[0]*10,
                        help='交替输入必选海报及其固定位置, 不选则填0, 以空格分割')
    # parser.add_argument('-mc', '--mandatory_characters', type=int, nargs=10,  # TODO(Frocean): set default after test.
    #                     default=[150010, 0, 150020, 0, 150030, 0, 150040, 0, 0, 0],
    #                     help='交替输入必选角色及其固定位置, 不选则填0, 以空格分割')
    # parser.add_argument('-mp', '--mandatory_posters', type=int, nargs=10,
    #                     default=[330250, 150030, 230120, 150040, 0, 0, 0, 0, 0, 0],
    #                     help='交替输入必选海报及其绑定角色, 不选则填0, 以空格分割')
    parser.add_argument('-ml', '--mandatory_leader', type=int, default=0, help='固定队长位置, 不选则填0')
    parser.add_argument('-u', '--update', type=str, default='https://github.com/esterTion/yumesute_master_db_diff')
    return parser.parse_args()


def parse_args_ob():
    parser = argparse.ArgumentParser(description='Yumesute auto team-up')
    parser.add_argument('user', nargs='?', metavar='File name for user data', default='Yumetest.json', help='账号数据名称')
    parser.add_argument('-d', '--data', metavar='DIR for server data', default='data', help='服务器内资源路径')
    parser.add_argument('-mc', '--mandatory_characters', type=int, nargs=10, default=[0]*10,
                        help='交替输入必选角色及其固定位置, 不选则填0, 以空格分割')
    parser.add_argument('-mp', '--mandatory_posters', type=int, nargs=10, default=[0]*10,
                        help='交替输入必选海报及其固定位置, 不选则填0, 以空格分割')
    parser.add_argument('-ml', '--mandatory_leader', type=int, default=0, help='固定队长位置, 不选则填0')
    parser.add_argument('-u', '--update', type=str, default='https://github.com/esterTion/yumesute_master_db_diff')
    return parser.parse_args()
