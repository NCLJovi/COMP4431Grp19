"""Knowledge base: red-flag rules, mitigating rules and compound (chained) rules.

`weight` here is the hand-set starting value. The GA in ga/tune.py writes its tuned values to
weights_tuned.json; this file is never overwritten. Rule names and reasons are in backend/wording.py.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..wording import RULE_TEXT


class _Worded:
    """Looks up the rule's text in backend/wording.py."""

    @property
    def name(self) -> str:
        return RULE_TEXT[self.id]["name"]

    @property
    def name_zh(self) -> str:
        return RULE_TEXT[self.id]["name_zh"]

    @property
    def why_en(self) -> str:
        return RULE_TEXT[self.id]["why_en"]

    @property
    def why_zh(self) -> str:
        return RULE_TEXT[self.id]["why_zh"]


@dataclass(frozen=True)
class Rule(_Worded):
    id: str
    category: str
    weight: float
    patterns: tuple[str, ...] = ()
    negatable: bool = False  # ignore a match when it is negated, e.g. "never share your OTP"


@dataclass(frozen=True)
class CompoundRule(_Worded):
    id: str
    category: str
    weight: float
    requires: tuple[frozenset[str], ...] = ()  # every group needs at least one fact


def _any(*facts: str) -> frozenset[str]:
    return frozenset(facts)


ASK_VERB_EN = r"(?:send|give|provide|tell|share|reply|enter|confirm|verify|input|read|key in|update|submit)"
SECRET_EN = r"(?:otp|one[- ]time (?:password|code|passcode)|verification code|sms code|password|passcode|\bpin\b|cvv|security code)"
ASK_VERB_ZH = r"(?:提供|告訴|告诉|話俾|話畀|俾|畀|輸入|输入|回覆|回复|填寫|填写|發送|发送|提交|讀出|读出|核實|核实|確認|确认)"
SECRET_ZH = r"(?:驗證碼|验证码|OTP|otp|一次性密碼|一次性密码|密碼|密码|CVV|安全碼|安全码)"

RULES: tuple[Rule, ...] = (
    Rule("R1", "pressure", 12,
         (r"(?:於|在)[^。！？\n]{0,8}(?:點|時|號|日)之?前", r"名額(?:只剩|有限|不多)|只剩最後", r"\d+\s*個?(?:工作天|工作日)", r"\burgent(?:ly)?\b", r"\b(?:verify|confirm|update|respond|reply|pay|log ?in)\b[^.!?\n,]{0,25}\bnow\b", r"\bimmediately\b", r"\bact now\b", r"\bright away\b", r"\bas soon as possible\b",
          r"\bfinal (?:notice|reminder|warning)\b", r"\blast chance\b", r"\bexpires? (?:today|tonight|soon)\b",
          r"\bwithin (?:\d+|one|two|24|48) (?:hours?|hrs?|minutes?|mins?)\b", r"\btoday only\b",
          r"立即", r"即時", r"即刻", r"马上", r"馬上", r"盡快", r"尽快", r"限時", r"限时", r"最後通知", r"最后通知",
          r"\d+\s*(?:小時|小时|個鐘|分鐘|分钟)內", r"今日內", r"今天內", r"逾期")),
    Rule("R2", "pressure", 14,
         (r"\b(?:account|card|service|number|line)\b[^.!?\n]{0,40}\b(?:suspended|frozen|blocked|locked|terminated|deactivated|disabled|closed|hacked|compromised)\b",
          r"否則[^。！？\n]{0,15}(?:停用|註銷|收回|回收|凍結|封鎖|取消|刪除)", r"暫停供應|停止供應",
          r"\bwill be (?:suspended|frozen|blocked|locked|terminated|deactivated|disconnected|arrested|prosecuted)\b",
          r"\b(?:arrest warrant|legal action|prosecut\w+|lawsuit|fined?)\b",
          r"凍結", r"冻结", r"停用", r"停機", r"暫停服務", r"暂停服务", r"封鎖", r"封锁", r"拘捕", r"逮捕", r"通緝", r"通缉",
          r"法律行動", r"法律行动", r"起訴", r"起诉", r"檢控", r"检控", r"罰款", r"罚款")),
    Rule("R3", "credential", 28,
         (rf"{ASK_VERB_EN}\b[^.!?\n]{{0,30}}{SECRET_EN}", rf"{ASK_VERB_ZH}[^。！？\n]{{0,12}}{SECRET_ZH}",
          r"\bwhat(?:'s| is) (?:the|your) (?:otp|code|password|pin)\b"),
         True),
    Rule("R4", "credential", 22,
         (r"\b(?:confirm|verify)\b[^.!?\n]{0,20}\b(?:identity|account)\b",
          rf"{ASK_VERB_EN}\b[^.!?\n]{{0,40}}(?:hkid|id (?:card|number)|identity card|card (?:number|details)|credit card|bank (?:account|details|login)|date of birth|personal (?:details|information|info))",
          rf"{ASK_VERB_ZH}[^。！？\n]{{0,14}}(?:身份證|身份证|信用卡|卡號|卡号|銀行戶口|银行账户|銀行賬戶|網上銀行|网上银行|個人資料|个人资料|出生日期)"),
         True),
    Rule("R5", "payment", 18,
         (r"\b(?:transfer|wire|remit|deposit|pay)\b[^.!?\n]{0,40}\b(?:hk\$|hkd|\$|fee|money|funds?|amount|deposit|account|now|immediately)",
          r"\b(?:handling|delivery|customs|clearance|processing|release|redelivery|admin(?:istration)?|security) (?:fee|charge|deposit)\b",
          r"\bsafe(?:ty)? account\b", r"\bfps\b", r"存入資金|入金", r"\b(?:give|send|lend) (?:me|us) (?:\w+ )?(?:money|cash|funds)\b",
          r"轉帳", r"转账", r"轉賬", r"過數", r"过数", r"轉數快", r"转数快", r"匯款", r"汇款", r"入錢", r"入钱", r"付款", r"繳付", r"缴付", r"繳交",
          r"手續費", r"手续费", r"保證金", r"保证金", r"清關費", r"清关费", r"安全戶口", r"安全账户", r"監管戶口"),
         True),
    Rule("R6", "impersonation", 16,
         (r"\b(?:police|immigration (?:department|officer|office)|customs(?: and excise)?|high court|court|inland revenue|ird|public security|procuratorate|government officer|icac)\b",
          r"警察", r"警方", r"警署", r"入境處", r"入境处", r"海關", r"海关", r"法院", r"法庭", r"公安", r"檢察院", r"检察院", r"税務局", r"稅務局", r"税务局", r"廉署", r"衞生署", r"卫生署", r"水務署", r"稅務部門")),
    Rule("R7", "impersonation", 6,
         (r"\b(?:hsbc|hang seng|bank of china|boc|standard chartered|citibank|octopus|alipayhk|payme|sf express|hongkong post|hong kong post|dhl|fedex)\b",
          r"滙豐", r"汇丰", r"恒生", r"中銀", r"中银", r"渣打", r"八達通", r"八达通", r"順豐", r"顺丰", r"香港郵政", r"香港邮政", r"郵政局")),
    Rule("R8", "lure", 12,
         (r"\b(?:parcel|package|shipment|delivery)\b[^.!?\n]{0,50}\b(?:failed|unsuccessful|held|on hold|pending|undeliverable|returned|incomplete|suspended|could not|cannot|unable)\b",
          r"\b(?:update|confirm|incomplete|wrong|invalid)\b[^.!?\n]{0,30}\b(?:delivery )?address\b", r"\bredeliver\w*\b",
          r"派送失敗", r"派送失败", r"無法派送", r"无法派送", r"未能派送", r"重新派送", r"地址不完整", r"地址不全", r"地址有誤", r"包裹.{0,12}(?:滯留|滞留|扣留|退回|問題|问题|延誤)", r"(?:未能|無法|均未能)接通", r"滯留費")),
    Rule("R9", "lure", 16,
         (r"\bcongratulations\b", r"\bgrand pri[cz]e\b", r"\b(?:you(?:'ve| have)? won|winner|lucky draw|lottery|jackpot|claim your (?:prize|reward|gift)|free (?:gift|iphone|voucher)|cash reward)\b",
          r"中獎", r"中奖", r"獎金", r"奖金", r"幸運抽獎", r"幸运抽奖", r"領取.{0,6}(?:獎|奖|禮|礼)", r"恭喜.{0,8}(?:獲得|获得|得到)", r"免費.{0,4}(?:贈品|赠品|現金券)")),
    Rule("R10", "lure", 22,
         (r"\bguaranteed? (?:\w+ )?(?:returns?|profits?|income|earnings?)\b", r"\b(?:high|huge|risk[- ]free) (?:returns?|profits?)\b",
          r"\b(?:crypto|bitcoin|usdt|forex)\b[^.!?\n]{0,50}\b(?:profit|returns?|invest\w*|trading|mentor|signal)\b", r"\b\d+%\s*(?:daily|weekly|monthly|profit|returns?)\b",
          r"\binvestment (?:group|mentor|tutor|teacher)\b",
          r"保證[^。！？\n]{0,8}(?:獲利|盈利|利潤|收益|回報)", r"保證回報", r"保证回报", r"高回報", r"高回报", r"穩賺", r"稳赚", r"零風險", r"零风险", r"投資導師", r"投资导师", r"帶單", r"带单", r"內幕消息", r"内幕消息", r"貼士群")),
    Rule("R11", "lure", 20,
         (r"\b(?:part[- ]time|work from home|online job|simple tasks?)\b[^.!?\n]{0,60}\b(?:earn|hk\$|\$|salary|income|per day|daily|commission)",
          r"\b(?:earn|make) (?:hk\$|\$|hkd )?\d[\d,]*\b[^.!?\n]{0,20}\b(?:a day|per day|daily|per hour|an hour)\b", r"\blike (?:and subscribe|videos?)\b[^.!?\n]{0,40}\bearn",
          r"日賺", r"日赚", r"刷單", r"刷单", r"在家工作", r"高薪兼職", r"高薪兼职", r"網上兼職", r"网上兼职", r"兼職.{0,20}(?:佣金|傭金|日薪|時薪|賺)", r"每日.{0,6}賺")),
    Rule("R12", "pressure", 18,
         (r"\b(?:do not|don't|never|must not) (?:tell|inform|mention|discuss|contact)\b[^.!?\n]{0,30}\b(?:anyone|family|bank|police|others|relatives|children|staff)\b",
          r"\bkeep (?:this|it)\b[^.!?\n]{0,20}\b(?:secret|confidential|between us)\b", r"\bconfidential (?:investigation|case)\b",
          r"保密", r"唔好(?:話俾|話畀|同|講俾|講畀|話).{0,8}(?:人|屋企|銀行|家人|知)", r"不要(?:告訴|告诉|通知).{0,8}(?:任何人|家人|銀行|银行)", r"不可(?:告訴|告诉|透露)")),
    Rule("R13", "impersonation", 16,
         (r"\b(?:new number|changed my (?:number|phone)|lost my phone|broke my phone|phone (?:is )?broken)\b", r"\bguess who\b",
          r"估下我係邊個", r"估吓我係邊個", r"猜猜我是誰", r"猜猜我是谁", r"我換咗電話", r"我换咗电话", r"換咗(?:新)?(?:電話|號碼)", r"換了(?:新)?(?:電話|號碼)", r"电话坏了", r"電話壞咗")),
    Rule("R14", "lure", 10,
         (r"\b(?:add|contact|message|join|whatsapp|chat with)\b[^.!?\n]{0,30}\b(?:whatsapp|telegram|wechat|line id|signal)\b", r"\b(?:telegram|whatsapp) (?:group|channel)\b", r"\bt\.me/(?!login)", r"(?:TG|Telegram|WhatsApp|微信)\s*(?:客服|群|號)", r"加我\s*(?:WA|WhatsApp|Whatsapp|微信|Line)",
          r"加.{0,8}(?:whatsapp|WhatsApp|telegram|Telegram|微信|WeChat)", r"(?:whatsapp|WhatsApp|telegram|Telegram)\s*群組?")),
    Rule("R15", "link", 10,
         (r"\bpress (?:the|this) (?:following )?link\b", r"\b(?:click|tap|visit|open|follow|log ?in (?:at|via|here)|sign ?in (?:at|via|here))\b[^.!?\n]{0,30}\b(?:link|here|below|url|website|site|portal|now)\b",
          r"\bclick\b", r"(?:點擊|点击|撳|㩒|按此|登入|前往|打開|打开).{0,10}(?:連結|链接|網址|网址|網站|网站|以下|此處|入面)", r"按此", r"請點擊", r"请点击"),
         True),
    Rule("R16", "link", 5,
         (r"https?://\S+", r"\bwww\.\S+", r"\b[a-z0-9-]+\.(?:com|net|org|hk|top|xyz|cc|icu|vip|shop|click|info|site|online)\b(?:/\S*)?")),
    Rule("R17", "device", 24,
         (r"\b(?:anydesk|teamviewer|rustdesk|\.apk)\b", r"\b(?:download|install)\b[^.!?\n]{0,30}\b(?:app|apk|software|program|application)\b",
          r"(?:下載|下载|安裝|安装)[^。！？\n]{0,12}(?:程式|程序|軟件|软件|應用|应用|APP|App|app|apk)"),
         True),
    Rule("R18", "payment", 22,
         (r"\b(?:gift ?cards?|apple cards?|steam cards?|google play cards?)\b", r"\b(?:pay|send|transfer|deposit)\b[^.!?\n]{0,30}\b(?:usdt|bitcoin|btc|crypto|ethereum)\b",
          r"禮品卡", r"礼品卡", r"點卡", r"点卡", r"比特幣", r"比特币", r"泰達幣", r"(?:轉|过|過|付).{0,6}(?:USDT|usdt|虛擬貨幣|虚拟货币)")),
    Rule("R19", "lure", 12,
         (r"\b(?:tax )?refund\b[^.!?\n]{0,40}\b(?:claim|click|receive|eligible|pending|apply|link|collect)\b", r"\b(?:eligible|qualify) for\b[^.!?\n]{0,30}\b(?:refund|subsidy|allowance|rebate)\b", r"\bclaim (?:your )?(?:refund|subsidy|rebate)\b",
          r"退稅", r"退税", r"退款.{0,12}(?:領取|领取|申請|申请|連結|连结|點擊|点击)", r"(?:領取|领取|申請|申请).{0,10}(?:津貼|津贴|補貼|补贴|退款)")),
    Rule("R20", "pressure", 12,
         (r"\bpress (?:\d|one|two|nine|zero)\b", r"\b(?:this is|you are hearing) an? (?:automated|recorded)\b",
          r"按\s*[0-9一二九零]\s*字?", r"(?:語音|语音)(?:訊息|讯息|信箱).{0,10}按")),
    Rule("R21", "pressure", 20,
         (r"\bmoney[- ]laundering\b", r"\b(?:your|an?) (?:identity|id|name|account|card)\b[^.!?\n]{0,50}\b(?:used|involved|linked|connected|associated|stolen)\b[^.!?\n]{0,40}\b(?:crime|criminal|fraud|illegal|smuggl\w+|case|investigation)\b", r"\billegal (?:items?|goods|parcel|drugs?)\b", r"\bsuspect(?:ed)? in\b",
          r"洗黑錢", r"洗黑钱", r"洗錢", r"洗钱", r"涉嫌", r"涉及.{0,10}(?:案件|案|犯罪|刑事)", r"身份.{0,8}(?:盜用|盗用|冒用)", r"違禁品", r"违禁品", r"非法物品", r"走私")),
    Rule("R22", "pressure", 18,
         (r"(?:帳號|賬號|帳戶|賬戶|戶口)[^。！？\n]{0,12}(?:未驗證|尚未驗證|未經驗證|異常|違規|風險|受限|限制|停用|註銷|凍結|封鎖|收回)",
          r"(?:限制|停用|收回|回收|註銷)[^。！？\n]{0,15}(?:使用權|功能|帳號|賬號|帳戶)",
          r"(?:驗證|認證|核實|解除|重新關聯|關聯)(?!碼)[^。！？\n]{0,8}(?:帳號|賬號|手機號碼|本機號碼|電話號碼|異常)",
          r"\b(?:account|number)\b[^.!?\n]{0,30}\b(?:not (?:yet )?verified|unverified|restricted|limited|flagged|violat\w+)\b",
          r"\bverify your (?:account|phone number|number)\b")),
    Rule("R23", "payment", 18,
         (r"(?:自動|將會|將於|即將)[^。！？\n]{0,12}(?:續費|扣款|扣除|扣數|收費|扣錢)",
          r"簽署[^。！？\n]{0,10}(?:合約|協議)",
          r"(?:會員|訂閱|服務|保單)[^。！？\n]{0,15}(?:到期|計費|扣除|扣取|扣費|收費|續費)",
          r"開始計費|扣除月費|產生費用|每[月年][^。！？\n]{0,10}扣",
          r"(?:取消|關閉|退訂|停止)[^。！？\n]{0,15}(?:致電|聯絡|撥打|聯繫|來電)",
          r"(?:致電|撥打|聯絡)[^。！？\n]{0,15}(?:取消|關閉|退訂)",
          r"\bauto(?:matically)?[- ]?renew\w*\b", r"\bwill be (?:charged|debited|deducted)\b",
          r"\bto cancel\b[^.!?\n]{0,30}\b(?:call|contact|phone)\b")),
    Rule("R24", "lure", 20,
         (r"投注|博彩|賭場|賭博|百家樂|真人娛樂|返水|流水|首充|上分|體育回贈|老虎機",
          r"\b(?:casino|betting|baccarat|sportsbook|slot games?|deposit bonus)\b")),
    Rule("R25", "lure", 8,
         (r"(?:致電|撥打|聯絡|聯繫|咨詢|諮詢|查詢|熱線|客服)[^。！？\n\d]{0,8}\d{4}[-\s]?\d{4}",
          r"\b(?:call|contact|phone|ring)\b[^.!?\n\d]{0,20}\d{4}[-\s]?\d{4}")),
    Rule("R26", "payment", 14,
         (r"尚未清繳|未繳|欠費|逾期未付|未清繳",
          r"\b(?:unpaid|overdue) (?:bill|balance|fee|payment)\b")),
    Rule("R27", "impersonation", 6,
         (r"鄰居|樓上|樓下|隔離屋", r"\bneighbou?r\b")),
    Rule("M1", "mitigating", -18,
         (r"\b(?:do not|don't|never|will never|won't)\b[^.!?\n]{0,30}\b(?:share|disclose|reveal|give|ask for|tell|forward)\b[^.!?\n]{0,40}\b(?:otp|code|password|pin|anyone|details)\b",
          r"\bif (?:this )?(?:this )?(?:was|wasn't|is|isn't)? ?(?:not )?(?:you|requested by you)\b",
          r"(?:請勿|请勿|切勿|不要|唔好|毋須|絕不會|绝不会)[^。！？\n]{0,14}(?:透露|分享|提供|轉發|转发|話俾|索取)[^。！？\n]{0,16}(?:驗證碼|验证码|密碼|密码|OTP|任何人|資料|资料)",
          r"(?:請勿|请勿|切勿|不要|唔好)[^。！？\n]{0,8}(?:任何人|他人|別人|别人)[^。！？\n]{0,6}(?:透露|提供|分享|話|讲|講)",
          r"提防騙|防騙|小心騙徒|提防騙徒")),
    Rule("M2", "mitigating", -14,
         (r"\b(?:official|our) (?:mobile )?(?:app|website|branch)\b", r"\b(?:number|hotline) on (?:the back of )?your card\b", r"\bvisit (?:any|your nearest|our) branch\b", r"\bno action (?:is )?(?:required|needed)\b",
          r"官方(?:應用|应用|程式|程序|網站|网站|app|App|APP)", r"卡背", r"親臨.{0,8}分行", r"亲临.{0,8}分行", r"毋須(?:採取|理會|回覆|操作)|無需(?:採取|回覆|操作)|無須(?:採取|回覆|操作)")),
    # This one is asserted by the URL inspector, not by a text pattern.
    Rule("M3", "mitigating", -16),
    Rule("U1", "link", 0),
)

COMPOUND_RULES: tuple[CompoundRule, ...] = (
    CompoundRule("C1", "compound", 14,
                 (_any("R7", "R8", "R19", "R26"), _any("R1", "R2"), _any("R15", "R16"))),
    CompoundRule("C2", "compound", 16,
                 (_any("R6"), _any("R2", "R21"))),
    CompoundRule("C3", "compound", 16,
                 (_any("R3", "R4"), _any("R1", "R2", "R15", "R16"))),
    CompoundRule("C4", "compound", 16,
                 (_any("R5", "R18", "R23"), _any("R1", "R2", "R6", "R12"))),
    CompoundRule("C5", "compound", 16,
                 (_any("R9", "R19"), _any("R3", "R4", "R5", "R15"))),
    CompoundRule("C6", "compound", 14,
                 (_any("R10", "R11", "R24"), _any("R5", "R14", "R15", "R16", "R18"))),
    CompoundRule("C7", "compound", 18,
                 (_any("R13"), _any("R5", "R18"))),
    CompoundRule("C10", "compound", 12,
                 (_any("R2"), _any("R1"))),
    CompoundRule("C11", "compound", 14,
                 (_any("R22"), _any("R1", "R2", "R4", "R15", "R16", "U1"))),
    CompoundRule("C12", "compound", 16,
                 (_any("R23"), _any("R25", "R1", "R2"))),
    CompoundRule("C13", "compound", 14,
                 (_any("R8"), _any("R25"))),
    CompoundRule("C14", "compound", 18,
                 (_any("R27"), _any("R14"))),
    # Chained rules: these depend on the conclusions above.
    CompoundRule("C8", "compound", 14,
                 (_any("C2"), _any("R3", "R4", "R5", "R12", "R18"))),
    CompoundRule("C9", "compound", 14,
                 (_any("U1"), _any("C1", "C3", "C5", "R1", "R2", "R3", "R4", "R8"))),
)

W_MATCH_DEFAULT = 25.0
W_URL_DEFAULT = 30.0
W_ML_DEFAULT = 15.0
