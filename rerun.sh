#/bin/bash
cd ..
mv findbiz_crawler findbiz_crawler_$1
git clone https://github.com/exactone/findbiz_crawler
cp -f findbiz_crawler_$1/all_json_out_json.json findbiz_crawler/.
cp -f findbiz_crawler_$1/all_json_out_json.json all_json_out_json.json.bk$1
rm -rf findbiz_crawler_$1/
cd findbiz_crawler/
source activate crawler
python crawler_v10.py $2 /usr/local/bin/phantomjs $1 1
