import numpy as np
import sys
import os
import pandas as pd
import json
import MyRiskFunctions
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
    

class saveFig():
    def __init__(self, jsonPath, threshold=0.02, limit=10):
        self.jsonPath = jsonPath
        self.threshold = threshold # threshold and limit are used for filtering low percentages components
        self.limit = limit

    def loadJson(self):
        with open('./outputJson/out.json', 'r') as f:
            out_json = json.load(f)

        out = {}
        for key, value in out_json.items():
            if isinstance(value, str):
                # 将字符串形式的JSON转换为Python对象
                out[key] = pd.read_json(json.dumps(json.loads(value)), orient='records')
            else:
                # 如果value不是字符串，直接转换
                out[key] = pd.read_json(json.dumps(value), orient='records')
        # out = {key: pd.read_json(value, orient='records') for key, value in out_json.items()}
        self.out = out

    def asset_allocation_comparison(self):
        x = range(len(self.out['assetAllocation']['categories']))
        plt.figure(figsize=(9, 3))
        plt.bar(x, self.out['assetAllocation']['last month'], width=0.4, label='Last Month', align='center')
        plt.bar([i + 0.4 for i in x], self.out['assetAllocation']['current'], width=0.4, label='Current', align='center')

        plt.xticks([i + 0.2 for i in x], self.out['assetAllocation']['categories'])

        plt.title('Last month and current month cash and securities percentages')
        plt.xlabel('Categories')
        plt.ylabel('Values')

        plt.legend()
        plt.savefig('figures/asset_allocation_comparison.png', bbox_inches='tight')
        plt.close()
    
    def cash(self):
        plt.figure(figsize=(3, 3))
        # filter 
        if len(self.out['CurrencyPer']['Currency']) > self.limit:
            df = self.out['CurrencyPer'].sort_values(by=['MV_USD'], ascending=False).head(self.limit)
            df_others = self.out['CurrencyPer']['Currency'].drop(df['Currency'].unique()).unique()
            # 对原数据中要合并为others的数据进行求和
            others_sum = self.out['CurrencyPer'][self.out['CurrencyPer']['Currency'].isin(df_others)].groupby('MV_USD').sum().reset_index()
            others_sum['Currency'] = 'others'
            # 将前limit条数据和合并后的数据进行合并
            df = pd.concat([df, others_sum])
        else:
            df = self.out['CurrencyPer']
        plt.pie(df['MV_USD'], labels=df['Currency'], autopct='%1.1f%%', startangle=90)
        plt.title('currency holding percentages')
        plt.savefig('figures/currency_holding_percentages.png', bbox_inches='tight')
        plt.close()

    def historicalPerformance(self):
        fig, ax = plt.subplots(figsize=(8, 4))

        self.out['clsp'].set_index('index', inplace=True)
        # 绘制折线图
        for holding in self.out['holdingUSDPer']['Holding'].to_list():
            if self.out['holdingUSDPer'][self.out['holdingUSDPer']['Holding'] == '1810.HK']['percentage'].iloc[0] >= 0.03:
                ax.plot(pd.to_datetime(self.out['clsp'].index), self.out['clsp'][holding], label=holding)
        holding_dict = self.out['holdingUSDPer'][['Holding', 'percentage', 'Currency']].set_index('Holding').to_dict()
        ax.plot(pd.to_datetime(self.out['clsp'].index), self.out['clsp']['p'], label='current portfolio backtest')
        # 设置图例
        ax.legend()

        # 设置标题和轴标签
        ax.set_title('Current portfolio and components historical performance(cumulative)')
        # 设置x轴的刻度定位器为每年的第一天
        plt.gca().xaxis.set_major_locator(mdates.YearLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        plt.grid()
        # 显示图表
        plt.savefig('figures/Holding_historical_performance(cumulative).png', bbox_inches='tight')
        plt.close()
    
    def historicalQuater(self):
        x = range(len(self.out['simu'].keys()))
        self.out['simu'].columns = pd.to_datetime(self.out['simu'].columns)
        years = self.out['simu'].columns.year
        quarters = self.out['simu'].columns.quarter
        new_columns = [f"{year}Q{quarter}" for year, quarter in zip(years, quarters)]
        self.out['simu'].columns = new_columns
        # self.out['simu'].columns = self.out['simu'].columns.astype(str)
        self.out['simu'] = self.out['simu'].sort_index(axis = 1, ascending = True)
        plt.figure(figsize=(9, 3))
        plt.bar(x, pd.DataFrame(self.out['simu']).T[0], width=0.4, label='drawdown', align='center')
        plt.bar([i + 0.4 for i in x], pd.DataFrame(self.out['simu']).T[1], width=0.4, label='gross return', align='center')

        plt.xticks([i + 0.2 for i in x], list(self.out['simu'].keys()))

        plt.title('Current portfolio performance in past Quaters')
        plt.xlabel('Categories')
        plt.ylabel('Values')

        plt.legend()
        plt.grid()
        plt.savefig('figures/historicalQuater.png', bbox_inches='tight')
        plt.close()
    
    def EquitiesStyle(self):
        plt.figure(figsize=(4, 3))
        self.out['StyleConcentration'].set_index('index', inplace=True)
        plt.barh(self.out['StyleConcentration'].index, self.out['StyleConcentration']['per'])
        # 设置标题和轴标签
        plt.title('Equities Percentage by Style')
        plt.xlabel('Style')
        plt.ylabel('Percentage')

        # 显示图表
        plt.savefig('figures/EquitiesStyle.png', bbox_inches='tight')
        plt.close()

    def EquitiesGICS(self):
        plt.figure(figsize=(4, 3))
        self.out['GICSConcentration'].set_index('index', inplace=True)
        plt.barh(self.out['GICSConcentration'].index, self.out['GICSConcentration']['per'])

        # 设置标题和轴标签
        plt.title('Equities Percentage by GICS')
        plt.xlabel('Percentage')
        plt.ylabel('GICS')

        # 显示图表
        plt.savefig('figures/EquitiesGICS.png', bbox_inches='tight')
        plt.close()

    
    # def EquitiesCR(self):
    #     plt.figure(figsize=(4, 3))
    #     self.out['CRConcentration'].set_index('index', inplace=True)
    #     plt.barh(self.out['CRConcentration'].index, self.out['CRConcentration']['per'])

    #     # 设置标题和轴标签
    #     plt.title('Equities Percentage by Credit Rating')
    #     plt.xlabel('Percentage')
    #     plt.ylabel('Credit Rating')

    #     # 显示图表
    #     plt.savefig('figures/EquitiesCR.png', bbox_inches='tight')
    #     plt.close()

    def corr(self):
        fig, ax = plt.subplots()
        data = self.out['corr']
        cax = ax.imshow(data, cmap='viridis')
        fig.colorbar(cax)

        # 设置行和列标签
        cols = list(data.columns)
        rows = cols
        ax.set_xticks(np.arange(len(cols)))
        ax.set_yticks(np.arange(len(rows)))
        ax.set_xticklabels(cols)
        ax.set_yticklabels(rows)

        data = np.array(data)

        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                ax.text(j, i, f'{np.array(data)[i, j]:.2f}', ha='center', va='center', color='white' if data[i, j] < 0.5 else 'black')

        # 旋转列标签以便于阅读
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        # 添加标题
        ax.set_title('Heatmap with assets')

        # 显示热力图
        plt.savefig('figures/corr.png', bbox_inches='tight')
        plt.close()
    def main(self):
        sf = saveFig(jsonPath=self.jsonPath)
        sf.loadJson()
        sf.asset_allocation_comparison()
        sf.cash()
        sf.historicalPerformance()
        sf.historicalQuater()
        sf.EquitiesStyle()
        sf.EquitiesGICS()
        # sf.EquitiesCR()
        sf.corr()

        # exp = explanation(sf.out)
        # exp.main()
    
class explanation():
    def __init__(self, out, jsonPath=None):
        self.jsonPath = jsonPath

    def explana_1(self):
        pass
    def save_explaJson(self):
        pass
    def main():
        pass
    



