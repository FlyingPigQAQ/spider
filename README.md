# Spider使用说明
## 基于python3编写
## 安装依赖
+ requests
+ fake_useragent
+ mysql
> eg: pip install requests
## 文件说明
+ bank.txt 全国银行信息
+ province.txt 全国省份信息
+ city.txt 全国地级市信息
> 文件在系统初始化时候会加载到内存中
## 使用方式
1. 如果想爬取某个银行，只需要在bank.txt加上该银行信息，格式如bank.txt.bak，省份，城市爬取操作相同。
2. 执行tobbyspider.py的主方法即可开始运行 
3. 数据库信息目前为mysql数据库，test库，bank表，后期可以提取到公共配置文件中
