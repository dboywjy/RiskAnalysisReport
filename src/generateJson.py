import numpy as np
import sys
import os
import pandas as pd
import json
import MyRiskFunctions
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from getHistoricalData import fetch_multiple_stocks, combine_data

categories = ['EQUITIES', 'FIXED INCOME & PREFERREDS', 'ALTERNATIVES', 'CASH']

class generateJson():
    def __init__(self, ClientInfo=None, currentTime=None):
        self.ClientInfo = ClientInfo
        self.currentTime = currentTime
        self.outputJson = {}

    def LoadClientInfo(self):
        """ 
        supposed to call the interface from AFE-N2N API,
        but at this time I use the clientInfo.json data
        """
        client = pd.read_json("./inputData/clientInfo.json")
        client['UpdateTime'] = pd.to_datetime(client['UpdateTime'], unit='ms').dt.strftime("%Y-%m-%d")
        client.sort_values(by=['UpdateTime'], inplace=True)
        self.client = client


    
    def getHistoricalData(self):
        """  
        get historical data from from AFE-N2N API,
        """
        # get data from AFE API
        stock_symbols = self.client[self.client['Type'] != "CASH"]['Holding'].tolist()  # List of stocks
        end_date = self.currentTime                    # End date
        start_date = (pd.to_datetime(end_date) - pd.DateOffset(years = 2)).strftime('%Y-%m-%d')
        period = "D"

        fetch_multiple_stocks(stock_symbols, start_date, end_date, period)
        cmd = combine_data(stock_symbols, start_date, end_date, period)
        his = cmd.merge()
        # output_file = f'./inputData/hisInputData.csv'
        # his.to_csv(output_file)
        # his = pd.read_csv("./inputData/hisInputData.csv")
        his.set_index('date', inplace=True)
        his = his.pivot(columns='instrument', values=['close', 'volume'])
        his.sort_index(ascending=True, inplace=True)
        self.his = his

    def getCurrency2USD(self):
        """
        Since current fx rate is not easy to get,
        then I use last work date's FX from historical data
        """
        currency_list = self.client['Currency'].tolist()
        latestFX = []
        for currency in currency_list:
            if currency != "USD":
                fx = self.his['close'][f'{currency}/USD'].sort_index(ascending=False).values[0]
                latestFX.append(fx)
            else:
                latestFX.append(1)
        latestFX
        self.client['FX(toUSD)'] = latestFX
        

    def assetAllocation(self):
        """
        Comparison of Last Month and Current Values of category in categories
        """
        base1 = pd.DataFrame(columns=['categories'], data=categories)
        self.client['MV_USD'] = self.client['Qty']*self.client['CurrentPrice(Local Currency)']*self.client['FX(toUSD)']
        agg1 = self.client.groupby(['UpdateTime', 'Type']).agg(MV_USD_sum_Asset=pd.NamedAgg(column='MV_USD', aggfunc='sum')).reset_index()
        agg2 = self.client.groupby(['UpdateTime']).agg(MV_USD_sum=pd.NamedAgg(column='MV_USD', aggfunc='sum')).reset_index()
        agg3 = pd.merge(agg1, agg2, how='left', left_on='UpdateTime', right_on='UpdateTime')
        agg3['percentage'] = agg3['MV_USD_sum_Asset']/ agg3['MV_USD_sum']
        agg3.set_index('Type', inplace=True)
        agg3 = agg3.pivot(columns='UpdateTime', values='percentage')
        agg3.reset_index(inplace=True)
        agg4 = pd.merge(base1, agg3, how='left', left_on='categories', right_on='Type')
        agg4.drop(columns=['Type'], inplace=True)
        agg4.columns = ['categories', 'last month', 'current']
        agg4.fillna(0, inplace=True)
        agg4['difference'] = agg4['current'] - agg4['last month']
        self.outputJson['assetAllocation'] = agg4
    
    def CurrencyPer(self):
        """
        Currency holding percentages(only cash)
        """
        cond1 = self.client['UpdateTime'] == self.client['UpdateTime'].min() # remember to change to max
        cond2 = self.client['Type'] == 'CASH'
        agg1 = self.client[cond1 & cond2] 

        self.outputJson['CurrencyPer'] = agg1[['Currency', 'MV_USD']]

    def closePriceModified(self):
        """
        modify close price to make them in USD
        agg1: 
            current holding each components' percentages in USD
        clsp:
            historical holding each components' percentages in USD
        """

        # current holding each components' percentages:
        cond1 = self.client['UpdateTime'] == self.client['UpdateTime'].max()
        agg1 = self.client[cond1]
        agg1['percentage'] = agg1['MV_USD'] / agg1['MV_USD'].sum()
        agg1[['Holding', 'percentage', 'Currency']] # used to backtesting
        holding_dict = agg1[['Holding', 'percentage', 'Currency']].set_index('Holding').to_dict()

        clsp = self.his['close']
        # in USD
        for holding in agg1['Holding'].to_list():
            if holding_dict['Currency'][holding] == 'USD':
                clsp[holding] = clsp[holding]
            else:
                clsp[holding] = clsp[holding]*clsp[holding_dict['Currency'][holding]+'/USD']
        init_price = {}
        for holding in agg1['Holding'].to_list():
            init_price[holding] = clsp[clsp[holding].isnull() == False][holding].to_list()[0]
            clsp[holding] = clsp[holding] / init_price[holding]
        
        p = np.dot(np.array(clsp[agg1['Holding'].to_list()]), np.array(list(holding_dict['percentage'].values())).reshape(-1, 1))
        clsp['p'] = p
        clsp['index'] = clsp.index
        self.outputJson['clsp'] = clsp
        self.outputJson['holdingUSDPer'] = agg1
        self.holding_dict = holding_dict
    
    def riskmetric(self):
        """
        calculate riskmetric using 
        """
        riskmetric = {}
        for holding in self.outputJson['holdingUSDPer']['Holding'].to_list():
            metrics = {}
            # holding percentage
            metrics['percentage'] = self.holding_dict['percentage'][holding]
            # current holding's gross_return in past 1 month
            date = pd.to_datetime(self.currentTime)
            # 找到前一个月的日期
            m1Date = (date - pd.DateOffset(months=1)).strftime('%Y-%m-%d')
            priceTemp = self.his['close']
            priceTemp = priceTemp[priceTemp.index >= m1Date]
            returns = priceTemp[holding].pct_change().dropna()
            metrics['gross_return(1m)'] = MyRiskFunctions.gross_return(returns)
            metrics['max drawdown(1m)'] = MyRiskFunctions.drawdown(returns)
            metrics['volatility(1m)'] = MyRiskFunctions.volatility(returns)
            
            # 找到前3个月的日期
            m1Date = (date - pd.DateOffset(months=3)).strftime('%Y-%m-%d')
            priceTemp = self.his['close']
            priceTemp = priceTemp[priceTemp.index >= m1Date]
            returns = priceTemp[holding].pct_change().dropna()
            metrics['gross_return(3m)'] = MyRiskFunctions.gross_return(returns)
            metrics['max drawdown(3m)'] = MyRiskFunctions.drawdown(returns)
            metrics['volatility(3m)'] = MyRiskFunctions.volatility(returns)

            # 找到前6个月的日期
            m1Date = (date - pd.DateOffset(months=6)).strftime('%Y-%m-%d')
            priceTemp = self.his['close']
            priceTemp = priceTemp[priceTemp.index >= m1Date]
            returns = priceTemp[holding].pct_change().dropna()
            metrics['gross_return(6m)'] = MyRiskFunctions.gross_return(returns)
            metrics['max drawdown(6m)'] = MyRiskFunctions.drawdown(returns)
            metrics['volatility(6m)'] = MyRiskFunctions.volatility(returns)
            riskmetric[holding] = metrics
        riskmetric = pd.DataFrame.from_dict(riskmetric, orient='index')

        riskmetric.index.name = 'instrument'
        riskmetric['instrument'] = riskmetric.index
        self.outputJson['riskmetric'] = riskmetric

    def marketRisk(self):
        """
        calculate market risk for portfilio
        """
        marketrisk = {}
        for holding in self.outputJson['holdingUSDPer']['Holding'].to_list():
            metrics = {}
            # holding percentage
            metrics['percentage'] = self.holding_dict['percentage'][holding]
            # current holding's contribution in past 1 month
            date = pd.to_datetime(self.currentTime)
            # 找到前一个月的日期
            priceTemp = self.his['close']
            returns = priceTemp[holding].pct_change().dropna()
            metrics['VaR'] = MyRiskFunctions.VaR_Hist(returns)
            metrics['CVaR'] = MyRiskFunctions.CVaR_Hist(returns)
            # metrics['volatility(1m)'] = MyRiskFunctions.volatility(returns)


            marketrisk[holding] = metrics


        marketrisk = pd.DataFrame.from_dict(marketrisk, orient='index')

        rc, portfolio_std_dev = MyRiskFunctions.risk_contribution(np.array(list(self.holding_dict['percentage'].values())), self.his['close'][list(self.holding_dict['percentage'].keys())])
        marketrisk['risk_contribution'] = rc / portfolio_std_dev
        marketrisk.index.name = 'instrument'
        marketrisk['instrument'] = marketrisk.index
        self.outputJson['marketrisk'] = marketrisk

        criterion = (marketrisk['risk_contribution'] * marketrisk['VaR']).sum()
        if criterion > 0 and criterion <= 0.01:
            level = 'very low risk'
        elif criterion > 0.01 and criterion <= 0.03:
            level = 'low risk'
        elif criterion > 0.03 and criterion <= 0.05:
            level = 'median risk'
        elif criterion > 0.05 and criterion <= 0.1:
            level = 'high risk'
        else:
            level = 'very high risk'
        level = pd.DataFrame(columns=['risk_level'], data=[level])
        self.outputJson['risk_level'] = level
        
    def hypotheticalPerformace(self):
        """

        """
        priceTemp = self.his['close']
        p = np.dot(np.array(self.outputJson['clsp'][self.outputJson['holdingUSDPer']['Holding'].to_list()]), np.array(list(self.holding_dict['percentage'].values())).reshape(-1, 1))
        priceTemp['portfolio'] = p
        priceTemp['Quarter'] = pd.to_datetime(priceTemp.index).to_period('Q')
        simu = {}
        quaters = priceTemp['Quarter'].value_counts()
        for q in quaters[quaters >= 50].index:
            metrics = {}
            dfq = priceTemp[priceTemp['Quarter'] == q]
            po = dfq['portfolio'].pct_change().dropna()
            metrics['drawdown'] = MyRiskFunctions.drawdown(po)
            metrics['gross_return'] = MyRiskFunctions.gross_return(po)

            simu[q] = metrics
        # simu = pd.DataFrame(simu).T
        # simu.index = simu.index.astype(str)
        self.outputJson['simu'] = pd.DataFrame(simu)

    def ADTV(self):
        adtv = {}
        for holding in self.outputJson['holdingUSDPer']['Holding'].to_list():
            metric = {}
            volumetemp = self.his['volume']
            t1 = int(volumetemp[holding].tail(30).mean())
            t2 = self.client[(self.client['UpdateTime'] == self.client['UpdateTime'].max()) & (self.client['Holding'] == holding)]['Qty'].tolist()[0]
            metric['ADTV'] = t1
            metric['Holding'] = t2
            metric['Holding/ADTV'] = t2/t1
            metric['instrument'] = holding
            adtv[holding] = metric

        self.outputJson['adtv'] = pd.DataFrame(adtv).T

    def concentrationRisk(self):

        data = self.client[(self.client['UpdateTime'] == self.client['UpdateTime'].max()) & (self.client['MorningstarStyleBox'].isnull() == False)][['MorningstarStyleBox', 'MV_USD']]
        agg1 = data.groupby(['MorningstarStyleBox']).agg(per=pd.NamedAgg(column='MV_USD', aggfunc='sum'))
        agg1['per'] = agg1['per'] / agg1['per'].sum()
        agg1['index'] = agg1.index
        self.outputJson['StyleConcentration'] = agg1

        data = self.client[(self.client['UpdateTime'] == self.client['UpdateTime'].max()) & (self.client['GICS'].isnull() == False)][['GICS', 'MV_USD']]
        agg1 = data.groupby(['GICS']).agg(per=pd.NamedAgg(column='MV_USD', aggfunc='sum'))
        agg1['per'] = agg1['per'] / agg1['per'].sum()
        agg1['index'] = agg1.index
        self.outputJson['GICSConcentration'] = agg1

        # data = self.client[(self.client['UpdateTime'] == self.client['UpdateTime'].max()) & (self.client['Credit Rating'].isnull() == False)][['Credit Rating', 'MV_USD']]
        # data['Credit Rating'] = data['Credit Rating'].apply(lambda x: x.split(',')[0])
        # agg1 = data.groupby(['Credit Rating']).agg(per=pd.NamedAgg(column='MV_USD', aggfunc='sum'))
        # agg1['per'] = agg1['per'] / agg1['per'].sum()
        # agg1['index'] = agg1.index
        # self.outputJson['CRConcentration'] = agg1

    def correlation(self):
        Target_assets = self.client[self.client['UpdateTime'] == self.client['UpdateTime'].max()]['Holding'].to_list()
        # Filter: 占比小于5%直接drop
        for asset in Target_assets:
            if self.holding_dict['percentage'][asset] < 0.05:
                Target_assets.remove(asset)

        temp = self.outputJson['clsp'][Target_assets]
        data = MyRiskFunctions.calculate_correlation(temp.dropna())
        # cols = self.client[self.client['UpdateTime'] == self.client['UpdateTime'].max()]['Holding'].to_list()
        # cols = 
        # rows = cols
        data = pd.DataFrame(columns=Target_assets, data=data)
        self.outputJson['corr'] = data

    def toJson(self):
        """  
        """
        self.outputJson = {key: df.to_json(orient='records') for key, df in self.outputJson.items()}
        self.outputJson = {key: json.loads(value) for key, value in self.outputJson.items()}
        # to json
        with open('./outputJson/out.json', 'w') as f:
            json.dump(self.outputJson, f, indent=4)
    
    def main(self):
        gs = generateJson(ClientInfo=None, currentTime='2024-11-10')
        gs.LoadClientInfo()
        gs.getHistoricalData()
        gs.getCurrency2USD()
        gs.assetAllocation()
        gs.CurrencyPer()
        gs.closePriceModified()
        gs.riskmetric()
        gs.marketRisk()
        gs.hypotheticalPerformace()
        gs.ADTV()
        gs.concentrationRisk()
        gs.correlation()
        
        gs.toJson()