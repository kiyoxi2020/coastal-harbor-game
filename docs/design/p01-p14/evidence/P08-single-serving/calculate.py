"""P08 proposed design arithmetic only; not Godot implementation or acceptance."""
import json
from pathlib import Path

def simulate(default=False):
    player, market, restaurant, depot_cash, fund = 100, 1000, 300, 0, 10000
    households = [200]*5
    stock = dict.fromkeys(('clam','snail','lettuce','tomato'),0)
    depot = dict.fromkeys(stock,60)
    inventory = dict(clam=0 if default else 2, lettuce=0 if default else 2, snail=0 if default else 1, tomato=0 if default else 1)
    costs = dict(clam=4,snail=5,lettuce=6,tomato=10)
    prices = dict(clam=8,snail=10,lettuce=12,tomato=20)
    rows=[]
    for day in range(1,17 if default else 15):
        if default and day==1:
            player-=5; market+=5
        supply=0
        if default and day==3:
            player+=20; restaurant-=20; supply=20
            inventory['clam']+=1; inventory['lettuce']+=1
        for i in range(5):
            income=min(12,fund); fund-=income; households[i]+=income
        enabled=not default or day>=3
        staff=0
        if enabled:
            for i in range(2):
                if restaurant>=4:
                    restaurant-=4; households[i]+=4; staff+=1
        for item in stock:
            n=min(4-stock[item],depot[item],market//costs[item])
            market-=n*costs[item]; depot_cash+=n*costs[item]
            depot[item]-=n; stock[item]+=n
        produced=dict(salad=0,stew=0); purchase=supply
        for _ in range(staff*2):
            for recipe,inputs in [('salad',('clam','lettuce')),('stew',('snail','tomato'))]:
                missing=[item for item in inputs if inventory[item]==0]
                bill=sum(prices[item] for item in missing)
                if bill>restaurant or any(stock[item]<1 for item in missing):
                    continue
                restaurant-=bill; market+=bill; purchase+=bill
                for item in missing:
                    stock[item]-=1; inventory[item]+=1
                for item in inputs: inventory[item]-=1
                produced[recipe]+=1
                break
            else: break
        remaining=produced.copy(); sold=dict(salad=0,stew=0)
        for offset in range(5):
            i=((day-1)%5+offset)%5
            if not enabled: continue
            for recipe,price in [('salad',30),('stew',42)]:
                if remaining[recipe] and households[i]>=price:
                    remaining[recipe]-=1; sold[recipe]+=1
                    households[i]-=price; restaurant+=price
                    break
        assert not any(remaining.values()), 'These fixtures expect all meals sold'
        balances=[player,market,restaurant,sum(households),depot_cash,fund]
        assert sum(balances)==12400 and min(balances+households)>=0
        assert all(n>=0 for n in list(stock.values())+list(depot.values())+list(inventory.values()))
        sales=sold['salad']*30+sold['stew']*42
        rows.append(dict(day=day,balances=balances,households=households.copy(),market=stock.copy(),depot=depot.copy(),restaurant_stock=inventory.copy(),produced=produced,sold=sold,profit=sales-purchase-staff*4,served=sum(sold.values()),staff=staff))
    return rows

if __name__=='__main__':
    result={name:simulate(default) for name,default in [('independent',False),('default',True)]}
    Path(__file__).with_name('results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for name,rows in result.items():
        print(name)
        for row in rows:
            if row['day'] in (1,3,7,14,16): print(json.dumps(row,ensure_ascii=False))
        print('served',sum(r['served'] for r in rows),'demand',len(rows)*5)
