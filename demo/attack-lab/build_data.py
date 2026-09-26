#!/usr/bin/env python3
"""Author six synthetic illustrations from preserved HSK source snapshots; run on cloud only."""
import copy
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ORIGIN = "synthetic_counterfactual"
SOURCES = {
    "reentrancy": "0x0cf0299fe30586abf0e3da2044ebe8353f9556a828e7e647cb22736c4a731880",
    "faulty_access_control": "0x060bf66d6ef981545c79ae810d33db9afb8c7203eab7c785ece2e8feea7ef4f1",
    "price_manipulation": "0x00b50f715f9078e68ac42c9b969065d3d4071e4b3e6437d8a3a4246148adef3a",
}
TITLES = {"reentrancy": "重复提款", "faulty_access_control": "资金操作权限", "price_manipulation": "价格与抵押借款"}
DISCLAIMER = "六个样本均为手写假设模拟。真实 HSK 交易仅提供来源与操作模板，不表示原交易或原合约存在漏洞；未执行 EVM 重放，也未调用攻击检测模型。"


def number(value):
    return format(Decimal(str(value)), "f")


class Trace:
    def __init__(self, caller, target, method, balances, storage, roles, assumptions):
        self.order = 0
        self.m = {"origin": ORIGIN, "hypothetical": True,
                  "transaction": {"hash": None, "chain_id": None, "network": "hypothetical HSK-like EVM", "from": caller, "to": target, "method": method, "value": "0", "status": "success"},
                  "actor_roles": roles, "pre_state": {"balances": copy.deepcopy(balances), "storage": copy.deepcopy(storage)},
                  "assumptions": assumptions + ["All balances, calls, storage and actors in this specimen are hypothetical.", "Gas costs are omitted; quantities use display units, not raw token integers."],
                  "call_trace": [], "storage_accesses": [], "control_checks": [], "asset_transfers": []}
        self.balances = copy.deepcopy(balances)
        self.storage = copy.deepcopy(storage)

    def event(self, category, **fields):
        self.order += 1
        row = {"order": self.order, "hypothetical": True, **fields}
        self.m[category].append(row)
        return row

    def call(self, parent, sender, target, method, **args):
        cid = "c" + str(len(self.m["call_trace"]) + 1)
        self.event("call_trace", id=cid, parent_id=parent, **{"from": sender, "to": target}, method=method, arguments=args, result="success")
        return cid

    def read(self, cid, key):
        self.event("storage_accesses", call_id=cid, operation="read", key=key, value=copy.deepcopy(self.storage[key]))
        return self.storage[key]

    def write(self, cid, key, value):
        self.event("storage_accesses", call_id=cid, operation="write", key=key, before=copy.deepcopy(self.storage.get(key)), after=copy.deepcopy(value))
        self.storage[key] = copy.deepcopy(value)

    def check(self, cid, expression, observed, enforced=True):
        self.event("control_checks", call_id=cid, expression=expression, observed_value=observed, enforced=enforced, branch="continue" if observed or not enforced else "revert")

    def transfer(self, cid, sender, recipient, asset, amount):
        amount = Decimal(str(amount))
        self.event("asset_transfers", call_id=cid, **{"from": sender, "to": recipient}, asset=asset, amount=number(amount))
        for actor, change in ((sender, -amount), (recipient, amount)):
            self.balances[actor][asset] = number(Decimal(self.balances[actor][asset]) + change)
            assert Decimal(self.balances[actor][asset]) >= 0, (actor, asset)

    def finish(self):
        self.m["post_state"] = {"balances": self.balances, "storage": self.storage}
        return self.m


def specimen(kind, variant, trace, summary, rationale, steps, metrics, changes):
    model = trace.finish()
    balances = [{"actor": actor, "asset": asset, "before": before, "after": model["post_state"]["balances"][actor][asset],
                 "delta": number(Decimal(model["post_state"]["balances"][actor][asset]) - Decimal(before))}
                for actor, assets in model["pre_state"]["balances"].items() for asset, before in assets.items()]
    return {"id": kind + "-" + variant, "variant": variant, "origin": ORIGIN,
            "title_zh": "正常对照" if variant == "benign" else "注入攻击模式", "summary": summary,
            "changed_fields": changes, "model_result": None,
            "reference_annotation": {"author": "assistant scenario author", "basis": "predefined synthetic scenario", "attack_labels": [] if variant == "benign" else [kind], "rationale": rationale},
            "model_input": model, "display": {"steps": [{"order": i + 1, "title": title, "detail": detail, "kind": event_kind} for i, (title, detail, event_kind) in enumerate(steps)],
                                                    "balances_before_after": balances, "metrics": [{"label": a, "value": b, "unit": c} for a, b, c in metrics]}}


def vault(variant):
    attack = variant == "attack"
    t = Trace("initiator_a", "actor_a", "execute", {"toy_vault": {"HSK": "100"}, "actor_a": {"HSK": "0"}},
              {"credit.actor_a": "10", "other_depositors_claim": "90"}, {"initiator_a": "transaction initiator", "actor_a": "caller and contract receiver", "toy_vault": "custody contract"},
              ["withdraw reads credit, sends that amount, and assigns credit = 0; assignment timing is specified by the ordered events."])
    entry = t.call(None, "initiator_a", "actor_a", "execute")
    root = t.call(entry, "actor_a", "toy_vault", "withdraw", amount="10")
    frames, current = [], root
    for i in range(3 if attack else 1):
        frames.append(current)
        t.read(current, "credit.actor_a")
        t.check(current, "credit.actor_a >= 10", True)
        if not attack:
            t.write(current, "credit.actor_a", "0")
        payout = t.call(current, "toy_vault", "actor_a", "receive", amount="10")
        t.transfer(payout, "toy_vault", "actor_a", "HSK", "10")
        if attack and i < 2:
            current = t.call(payout, "actor_a", "toy_vault", "withdraw", amount="10")
    if attack:
        for cid in reversed(frames):
            t.write(cid, "credit.actor_a", "0")
    steps = [("读取提款额度", "actor_a 的可提款额度为 10 HSK。", "read"),
             ("先归零，再付款" if not attack else "额度仍未归零", "正常对照先将额度写为 0。" if not attack else "第一次付款后，接收合约回调同一提款函数，仍读到额度 10。", "write" if not attack else "call"),
             ("完成一次付款" if not attack else "两次回调、共三次付款", "金库向接收方支付 10 HSK。" if not attack else "每次都支付 10 HSK，共支付 30 HSK；三个栈帧随后都执行 credit = 0。", "transfer"),
             ("最终余额", "金库 90、接收方 10 HSK；额度 0。" if not attack else "金库 70、接收方 30 HSK；额度 0，其他存款人的 90 HSK 债权仍在。", "state")]
    return specimen("reentrancy", variant, t, "提款 10 HSK，先更新额度。" if not attack else "将额度更新后移，嵌套调用重复支付。",
                    "状态先更新，单次付款与额度一致。" if not attack else "两次嵌套回调在额度更新前重复读取同一额度；三次付款超过合法额度 20 HSK。", steps,
                    [("付款次数", "3" if attack else "1", "次"), ("超额提款", "20" if attack else "0", "HSK")],
                    ["用 toy_vault / actor_a 替代所有执行主体", "构造 100 HSK 金库及 10 HSK 额度", "构造付款与额度写入顺序，以及假设调用和资产转移"])


def authorization(variant):
    attack = variant == "attack"
    caller, recipient, amount = ("actor_a", "recipient_a", "40") if attack else ("actor_b", "recipient_b", "5")
    actors = ("toy_treasury", "actor_a", "actor_b", "recipient_a", "recipient_b")
    t = Trace(caller, "toy_treasury", "fund", {a: {"HSK": "100" if a == "toy_treasury" else "0"} for a in actors},
              {"authorized_role": ["actor_b"], "fixed_beneficiary": "recipient_b", "guard_enforced": not attack},
              {"toy_treasury": "fund custody contract", "actor_a": "caller account A", "actor_b": "caller account B", "recipient_a": "recipient account A", "recipient_b": "recipient account B"},
              ["Policy requires caller in authorized_role and recipient equal to fixed_beneficiary for every fund operation."])
    cid = t.call(None, caller, "toy_treasury", "fund", recipient=recipient, amount=amount)
    t.read(cid, "authorized_role")
    t.read(cid, "fixed_beneficiary")
    t.read(cid, "guard_enforced")
    t.check(cid, "caller in authorized_role", not attack, not attack)
    t.check(cid, "recipient == fixed_beneficiary", not attack, not attack)
    pay = t.call(cid, "toy_treasury", recipient, "receive", amount=amount)
    t.transfer(pay, "toy_treasury", recipient, "HSK", amount)
    return specimen("faulty_access_control", variant, t, "获授权主体向固定收款人拨款 5 HSK。" if not attack else "绕过权限分支，未授权主体向任意收款人转走 40 HSK。",
                    "角色与收款人两项约束均满足。" if not attack else "角色与收款人约束均不满足，但 guard_enforced=false 的假设路径仍完成转账。",
                    [("读取授权规则", "仅 actor_b 有权拨款；唯一允许收款人为 recipient_b。", "read"), ("检查调用者", "actor_b 通过角色检查。" if not attack else "actor_a 不在授权列表，检查结果未阻止执行。", "check"),
                     ("检查收款人", "recipient_b 符合固定收款人约束。" if not attack else "recipient_a 不符合固定收款人约束，检查结果未阻止执行。", "check"), ("执行拨款", f"toy_treasury → {recipient}：{amount} HSK。", "transfer")],
                    [("转出金额", amount, "HSK"), ("金库剩余", "60" if attack else "95", "HSK")],
                    ["将真实 fund 调用仅作为操作模板", "构造角色列表、固定收款人和权限分支", "构造调用者、收款人、金额与金库余额"])


def price(variant):
    attack = variant == "attack"
    balances = {"actor_a": {"HSK": "0" if attack else "100", "USDT": "0"}, "toy_pool": {"HSK": "1000", "USDT": "100000"},
                "toy_lender": {"HSK": "0", "USDT": "100000"}, "toy_flash": {"HSK": "0", "USDT": "200000"}}
    storage = {"pool.reserve_hsk": "1000", "pool.reserve_usdt": "100000", "reference_price_usdt_per_hsk": "100", "max_ltv": "0.75",
               "position.owner": "actor_a", "position.collateral_hsk": "0", "position.debt_usdt": "0", "flash.outstanding_usdt": "0", "oracle_source": "pool_spot" if attack else "independent_reference"}
    t = Trace("initiator_a", "actor_a", "execute", balances, storage, {"initiator_a": "transaction initiator", "actor_a": "borrower contract and position owner", "toy_pool": "constant-product liquidity pool", "toy_lender": "collateral custody and lending contract", "toy_flash": "flash liquidity provider"},
              ["Fee-free pool invariant starts at 100000000; swap output rounds down to 6 decimal USDT units.", "Flash fee is 90 USDT on 100000 USDT principal.", "Collateral is held by toy_lender; its HSK balance and position.collateral_hsk describe the same tokens.", "Position owner retains debt and collateral claim. No default or liquidation is executed. Independent reference price is assumed, not observed market data."])
    root = t.call(None, "initiator_a", "actor_a", "execute")
    parent = root
    if attack:
        flash = t.call(root, "actor_a", "toy_flash", "flashBorrow", amount="100000")
        t.transfer(flash, "toy_flash", "actor_a", "USDT", "100000")
        t.write(flash, "flash.outstanding_usdt", "100090")
        parent = t.call(flash, "toy_flash", "actor_a", "onLiquidity", amount="100000", fee="90")
        buy = t.call(parent, "actor_a", "toy_pool", "swap", input_asset="USDT", input_amount="100000")
        t.transfer(buy, "actor_a", "toy_pool", "USDT", "100000")
        t.transfer(buy, "toy_pool", "actor_a", "HSK", "500")
        t.write(buy, "pool.reserve_hsk", "500")
        t.write(buy, "pool.reserve_usdt", "200000")
    pledge = t.call(parent, "actor_a", "toy_lender", "depositCollateral", amount="100")
    t.transfer(pledge, "actor_a", "toy_lender", "HSK", "100")
    t.write(pledge, "position.collateral_hsk", "100")
    borrow = t.call(parent, "actor_a", "toy_lender", "borrow", amount="30000" if attack else "5000")
    for key in ("position.owner", "position.collateral_hsk", "position.debt_usdt", "max_ltv", "oracle_source"):
        t.read(borrow, key)
    for key in (("pool.reserve_hsk", "pool.reserve_usdt") if attack else ("reference_price_usdt_per_hsk",)):
        t.read(borrow, key)
    t.check(borrow, "caller == position.owner", True)
    t.check(borrow, "new_debt <= collateral * selected_price * max_ltv", True)
    t.event("control_checks", call_id=borrow, expression="selected_price_usdt_per_hsk", observed_value="400" if attack else "100", enforced=True, branch="continue")
    debt = "30000" if attack else "5000"
    t.write(borrow, "position.debt_usdt", debt)
    t.transfer(borrow, "toy_lender", "actor_a", "USDT", debt)
    if attack:
        sell = t.call(parent, "actor_a", "toy_pool", "swap", input_asset="HSK", input_amount="400")
        t.transfer(sell, "actor_a", "toy_pool", "HSK", "400")
        t.transfer(sell, "toy_pool", "actor_a", "USDT", "88888.888888")
        t.write(sell, "pool.reserve_hsk", "900")
        t.write(sell, "pool.reserve_usdt", "111111.111112")
        repay = t.call(parent, "actor_a", "toy_flash", "repay", amount="100090")
        t.transfer(repay, "actor_a", "toy_flash", "USDT", "100090")
        t.write(repay, "flash.outstanding_usdt", "0")
        t.check(flash, "flash.outstanding_usdt == 0", True)
    steps = [("取得临时资金", "闪借 100,000 USDT；需归还本金和费用 100,090。", "transfer"), ("买入并改变池内价格", "100,000 USDT 买入 500 HSK；储备变为 500 / 200,000，边际现货价升至 400 USDT/HSK。", "transfer"), ("抵押与借款", "抵押 100 HSK；读取被改变的池内价格，以 75% LTV 借出 30,000 USDT。", "read"), ("卖回剩余 HSK", "卖出 400 HSK，获得 88,888.888888 USDT；储备变为 900 / 111,111.111112。", "transfer"), ("归还闪借", "归还 100,090 USDT，账户剩余现金 18,798.888888 USDT；仍负债 30,000 USDT。", "transfer"), ("独立参考估值", "按假设参考价 100，抵押品值 10,000 USDT；债务超出其参考价值 20,000，尚未清算。", "state")] if attack else [("自有抵押品", "actor_a 初始持有 100 HSK；无需临时资金。", "state"), ("存入抵押品", "100 HSK 转入借贷合约托管，position.owner 保持 actor_a。", "transfer"), ("读取独立价格", "采用独立参考价 100 USDT/HSK；最大 LTV 75%，可借上限 7,500 USDT。", "read"), ("健康借款", "借出 5,000 USDT，LTV 为 50%；池储备与闪借资金均未变化。", "transfer")]
    return specimen("price_manipulation", variant, t, "使用自有抵押品和独立参考价格的健康借款。" if not attack else "同一交易中改变池内价格，再按该价格超额借款。",
                    "独立价格未依赖交易中的池内储备；5,000 债务由参考价值 10,000 的抵押品支持。" if not attack else "借贷读取同一交易刚改变的池内现货价，100 HSK 支持了 30,000 USDT 借款；按独立参考价，债务超过抵押品价值。",
                    steps, [("债务", debt, "USDT"), ("抵押品参考价值", "10000", "USDT"), ("闪借归还后剩余现金" if attack else "借款到账", "18798.888888" if attack else "5000", "USDT")],
                    ["真实 swap 交易只提供交换操作模板", "构造恒定乘积池、借贷协议、资金提供者与全部余额", "构造价格读取、抵押和借款；正常对照使用自有资金及独立价格"])


def main():
    rows = json.loads(Path(sys.argv[1]).read_text())
    indexed = {row["id"]: row for row in rows}
    groups = []
    for kind, builder in (("reentrancy", vault), ("faulty_access_control", authorization), ("price_manipulation", price)):
        row = indexed[SOURCES[kind]]
        state, tx = row["state"], row["state"]["transaction"]
        assert state["chain_id"] == 177 and tx["hash"].lower() == SOURCES[kind]
        canonical = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        source = {"hash": tx["hash"], "chain_id": 177, "method": tx["method"], "timestamp": tx["timestamp"], "block": tx["block_number"],
                  "explorer_url": "https://hashkey.blockscout.com/tx/" + tx["hash"], "state_sha256": hashlib.sha256(canonical).hexdigest(),
                  "upstream_state_sha256": row.get("state_sha256"), "original_state": copy.deepcopy(state), "usage": "provenance and operation template only"}
        groups.append({"id": kind, "title_zh": TITLES[kind], "attack_type": kind, "source_transaction": source, "variants": [builder("benign"), builder("attack")]})
    output = {"schema_version": "1.0.0", "origin": ORIGIN, "title_zh": "真实 HSK 来源 × 合成攻击模式", "disclaimer_zh": DISCLAIMER,
              "annotation_policy": {"author": "assistant scenario author", "model_run": False, "model_input_boundary": "Send only variant.model_input to a future detector; annotations, source metadata and display content are excluded."},
              "reference": {"paper": "Clue, arXiv:2305.14046v1", "url": "https://arxiv.org/html/2305.14046v1", "sections": ["5.3", "5.4", "5.5"], "use": "Three scenario families adapted for explanation; not a reproduction of Clue."}, "groups": groups}
    target = Path(sys.argv[2])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(target), "groups": len(groups), "specimens": sum(len(g["variants"]) for g in groups), "model_calls": 0}))


if __name__ == "__main__":
    main()
