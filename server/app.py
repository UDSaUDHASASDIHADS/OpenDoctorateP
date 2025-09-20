import re
import logging
from builtins import print
from datetime import datetime
import asyncio

# 同时导入Flask和FastAPI
from flask import Flask
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse

from utils import read_json, preload_json_data, start_global_event_loop
from constants import CONFIG_PATH

# 导入所有模块（保持不变）
import account, background, building, campaignV2, char, charBuild, charm, \
        crisis, deepsea, gacha, mail, online, tower, quest, pay, rlv2, shop, story, \
        user, asset.assetbundle, config.prod, social, templateShop, other, sandbox, charrotation, \
        activity, vecbreak, mission

server_config = read_json(CONFIG_PATH)

# 框架配置
use_fastapi = server_config["server"].get("useFastAPI", False)  # 新增配置项，控制使用哪个框架

# 根据配置创建相应的应用实例
if use_fastapi:
    app = FastAPI()
    api_router = APIRouter()
else:
    app = Flask(__name__)

host = server_config["server"]["host"]
port = server_config["server"]["port"]
useMemoryCache = server_config["server"]["useMemoryCache"]

# 日志配置（保持不变）
logger = logging.getLogger('werkzeug')
logger.setLevel(logging.INFO)
logger.addFilter(lambda record: not re.match(r'.*(/syncPushMessage|/pb/async|/event|/batch_event).*', record.getMessage()))

# 通用路由（保持不变）
app.add_url_rule("/app/getSettings", methods = ["POST"], view_func = user.appGetSettings)
app.add_url_rule("/app/getCode", methods = ["POST"], view_func = user.appGetCode)


# Account相关路由 - 完全使用FastAPI
if use_fastapi:
    # FastAPI路由注册（使用异步接口）
    api_router.add_api_route("/account/login", account.account_login, methods=["POST"])
    api_router.add_api_route("/account/syncData", account.account_sync_data, methods=["POST"])
    api_router.add_api_route("/account/syncStatus", account.account_sync_status, methods=["POST"])
    api_router.add_api_route("/account/yostar_auth_request", account.account_yostar_auth_request, methods=["POST"])
    api_router.add_api_route("/account/yostar_auth_submit", account.account_yostar_auth_submit, methods=["POST"])
    api_router.add_api_route("/account/syncPushMessage", account.sync_push_message, methods=["POST"])
    app.include_router(api_router)
else:
    
    from functools import wraps

    def flask_wrap(async_func):
        @wraps(async_func)
        def wrapper(*args, **kwargs):
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                # pass through args/kwargs to the async function
                result = loop.run_until_complete(async_func(*args, **kwargs))
                return result
            finally:
                try:
                    loop.close()
                except Exception:
                    pass
        return wrapper

    app.add_url_rule("/account/login", methods=["POST"], view_func=flask_wrap(account.account_login))
    app.add_url_rule("/account/syncData", methods=["POST"], view_func=flask_wrap(account.account_sync_data))
    app.add_url_rule("/account/syncStatus", methods=["POST"], view_func=flask_wrap(account.account_sync_status))
    app.add_url_rule("/account/yostar_auth_request", methods=["POST"], view_func=flask_wrap(account.account_yostar_auth_request))
    app.add_url_rule("/account/yostar_auth_submit", methods=["POST"], view_func=flask_wrap(account.account_yostar_auth_submit))
    app.add_url_rule("/account/syncPushMessage", methods=["POST"], view_func=flask_wrap(account.sync_push_message))



app.add_url_rule("/assetbundle/official/Android/assets/<string:assetsHash>/<string:fileName>", methods = ["GET"], view_func = asset.assetbundle.getFile)

app.add_url_rule("/background/setBackground", methods = ["POST"], view_func = background.SetBackground)
app.add_url_rule("/homeTheme/change", methods = ["POST"], view_func = background.homeThemeChange)

app.add_url_rule("/building/sync", methods=["POST"], view_func=building.Sync)
app.add_url_rule("/building/getRecentVisitors", methods=["POST"], view_func=building.GetRecentVisitors)
app.add_url_rule("/building/getInfoShareVisitorsNum", methods=["POST"], view_func=building.GetInfoShareVisitorsNum)
app.add_url_rule("/building/assignChar", methods=["POST"], view_func=building.AssignChar)
app.add_url_rule("/building/changeDiySolution", methods=["POST"], view_func=building.ChangeDiySolution)
app.add_url_rule("/building/changeManufactureSolution", methods=["POST"], view_func=building.ChangeManufactureSolution)
app.add_url_rule("/building/settleManufacture", methods=["POST"], view_func=building.SettleManufacture)
app.add_url_rule("/building/workshopSynthesis", methods=["POST"], view_func=building.WorkshopSynthesis)
app.add_url_rule("/building/upgradeSpecialization", methods=["POST"], view_func=building.UpgradeSpecialization)
app.add_url_rule("/building/completeUpgradeSpecialization", methods=["POST"], view_func=building.CompleteUpgradeSpecialization)
app.add_url_rule("/building/deliveryOrder", methods=["POST"], view_func=building.DeliveryOrder)
app.add_url_rule("/building/deliveryBatchOrder",methods=["POST"], view_func=building.DeliveryBatchOrder)
app.add_url_rule("/building/cleanRoomSlot", methods=["POST"], view_func=building.CleanRoomSlot)
app.add_url_rule("/building/getAssistReport", methods=["POST"], view_func=building.getAssistReport)
app.add_url_rule("/building/setBuildingAssist", methods=["POST"], view_func=building.setBuildingAssist)
app.add_url_rule("/building/degradeRoom", methods=["POST"], view_func=building.changRoomLevel)
app.add_url_rule("/building/upgradeRoom", methods=["POST"], view_func=building.changRoomLevel)
app.add_url_rule("/building/changeStrategy", methods=["POST"], view_func=building.changeStrategy)
app.add_url_rule("/building/addPresetQueue", methods=["POST"], view_func=building.addPresetQueue)
app.add_url_rule("/building/deletePresetQueue", methods=["POST"], view_func=building.deletePresetQueue)
app.add_url_rule("/building/editPresetQueue", methods=["POST"], view_func=building.editPresetQueue)
app.add_url_rule("/building/usePresetQueue", methods=["POST"], view_func=building.usePresetQueue)
app.add_url_rule("/building/editLockQueue", methods=["POST"], view_func=building.editLockQueue)
app.add_url_rule("/building/batchRestChar", methods=["POST"], view_func=building.batchRestChar)
app.add_url_rule("/building/buildRoom", methods=["POST"], view_func=building.buildRoom)
app.add_url_rule("/building/getClueBox", methods=["POST"], view_func=building.getClueBox)
app.add_url_rule("/building/getClueFriendList", methods=["POST"], view_func=building.getClueFriendList)
app.add_url_rule("/building/changeBGM", methods = ["POST"], view_func=building.changeBGM)
app.add_url_rule("/building/setPrivateDormOwner", methods=["POST"], view_func=building.setPrivateDormOwner)

app.add_url_rule("/campaignV2/battleStart", methods = ["POST"], view_func = campaignV2.campaignV2BattleStart)
app.add_url_rule("/campaignV2/battleFinish", methods = ["POST"], view_func = campaignV2.campaignV2BattleFinish)
app.add_url_rule("/campaignV2/battleSweep", methods = ["POST"], view_func = campaignV2.campaignV2BattleSweep)

app.add_url_rule("/char/changeMarkStar", methods = ["POST"], view_func = char.charChangeMarkStar)

app.add_url_rule("/charBuild/addonStage/battleStart", methods = ["POST"], view_func = quest.questBattleStart)
app.add_url_rule("/charBuild/addonStage/battleFinish", methods = ["POST"], view_func = quest.questBattleFinish)
app.add_url_rule("/charBuild/addonStory/unlock", methods = ["POST"], view_func = charBuild.charBuildaddonStoryUnlock)
app.add_url_rule("/charBuild/batchSetCharVoiceLan", methods = ["POST"], view_func = charBuild.charBuildBatchSetCharVoiceLan)
app.add_url_rule("/charBuild/setCharVoiceLan", methods = ["POST"], view_func = charBuild.charBuildSetCharVoiceLan)
app.add_url_rule("/charBuild/setDefaultSkill", methods = ["POST"], view_func = charBuild.charBuildSetDefaultSkill)
app.add_url_rule("/charBuild/changeCharSkin", methods = ["POST"], view_func = charBuild.charBuildChangeCharSkin)
app.add_url_rule("/charBuild/setEquipment", methods = ["POST"], view_func = charBuild.charBuildSetEquipment)
app.add_url_rule("/charBuild/changeCharTemplate", methods = ["POST"], view_func = charBuild.charBuildChangeCharTemplate)

app.add_url_rule("/charm/setSquad", methods = ["POST"], view_func = charm.charmSetSquad)

app.add_url_rule("/config/prod/announce_meta/Android/preannouncement.meta.json", methods = ["GET"], view_func = config.prod.prodPreAnnouncement)
app.add_url_rule("/config/prod/announce_meta/Android/announcement.meta.json", methods = ["GET"], view_func = config.prod.prodAnnouncement)
app.add_url_rule("/config/prod/official/Android/version", methods = ["GET"], view_func = config.prod.prodAndroidVersion)
app.add_url_rule("/config/prod/official/network_config", methods = ["GET"], view_func = config.prod.prodNetworkConfig)
app.add_url_rule("/config/prod/official/refresh_config", methods = ["GET"], view_func = config.prod.prodRefreshConfig)
app.add_url_rule("/config/prod/official/remote_config", methods = ["GET"], view_func = config.prod.prodRemoteConfig)
app.add_url_rule("/api/game/get_latest_game_info", methods = ["GET"], view_func= config.prod.get_latest_game_info)
app.add_url_rule("/api/gate/meta/Android", methods = ["GET"], view_func= config.prod.prodGateMeta)
app.add_url_rule("/api/remote_config/101/prod/default/Android/ak_sdk_config", methods = ["GET"], view_func= config.prod.ak_sdk_config)

app.add_url_rule("/crisis/getInfo", methods = ["POST"], view_func = crisis.crisisGetCrisisInfo)
app.add_url_rule("/crisis/battleStart", methods = ["POST"], view_func = crisis.crisisBattleStart)
app.add_url_rule("/crisis/battleFinish", methods = ["POST"], view_func = crisis.crisisBattleFinish)
app.add_url_rule("/crisisV2/getInfo", methods = ["POST"], view_func = crisis.crisisV2_getInfo)
app.add_url_rule("/crisisV2/confirmMissions", methods = ["POST"], view_func = crisis.crisisV2_confirmMissions)
app.add_url_rule("/crisisV2/battleStart", methods = ["POST"], view_func = crisis.crisisV2_battleStart)
app.add_url_rule("/crisisV2/battleFinish", methods = ["POST"], view_func = crisis.crisisV2_battleFinish)
app.add_url_rule("/crisisV2/getSnapshot", methods = ["POST"], view_func = crisis.crisisV2_getSnapshot)
app.add_url_rule("/crisisV2/getGoodList", methods = ["POST"], view_func = crisis.crisisV2_getGoodList)

app.add_url_rule("/deepSea/branch", methods = ["POST"], view_func = deepsea.deepSeaBranch)
app.add_url_rule("/deepSea/event", methods = ["POST"], view_func = deepsea.deepSeaEvent)

app.add_url_rule("/mail/getMetaInfoList", methods = ["POST"], view_func = mail.mailGetMetaInfoList)
app.add_url_rule("/mail/listMailBox", methods = ["POST"], view_func = mail.mailListMailBox)
app.add_url_rule("/mailCollection/getList", methods = ["POST"], view_func = mail.mailCollectionGetList)
app.add_url_rule("/mail/receiveMail", methods = ["POST"], view_func = mail.mailReceiveMail)
app.add_url_rule("/mail/receiveAllMail", methods = ["POST"], view_func = mail.mailReceiveAllMail)
app.add_url_rule("/mail/removeAllReceivedMail", methods = ["POST"], view_func = mail.mailRemoveAllReceivedMail)

app.add_url_rule("/online/v1/ping", methods = ["POST"], view_func = online.onlineV1Ping)
app.add_url_rule("/online/v1/loginout", methods = ["POST"], view_func = online.onlineV1LoginOut)
app.add_url_rule("/user/online/v1/loginout", methods = ["POST"], view_func = online.onlineV1LoginOut)

app.add_url_rule("/tower/createGame", methods = ["POST"], view_func = tower.towerCreateGame)
app.add_url_rule("/tower/initGodCard", methods = ["POST"], view_func = tower.towerInitGodCard)
app.add_url_rule("/tower/initGame", methods = ["POST"], view_func = tower.towerInitGame)
app.add_url_rule("/tower/initCard", methods = ["POST"], view_func = tower.towerInitCard)
app.add_url_rule("/tower/battleStart", methods = ["POST"], view_func = tower.towerBattleStart)
app.add_url_rule("/tower/battleFinish", methods = ["POST"], view_func = tower.towerBattleFinish)
app.add_url_rule("/tower/recruit", methods = ["POST"], view_func = tower.towerRecruit)
app.add_url_rule("/tower/chooseSubGodCard", methods = ["POST"], view_func = tower.towerChooseSubGodCard)
app.add_url_rule("/tower/settleGame", methods = ["POST"], view_func = tower.towerSettleGame)

app.add_url_rule("/pay/getUnconfirmedOrderIdList", methods=["POST"], view_func=pay.GetUnconfirmedOrderIdList)
app.add_url_rule("/u8/pay/getAllProductList", methods=["POST"], view_func=pay.getAllProductList)
app.add_url_rule("/pay/createOrder", methods=["POST"], view_func=pay.getcreateOrder)
app.add_url_rule("/pay/v1/query_show_app_product", methods=["POST"], view_func=pay.queryshowappproduct)
app.add_url_rule("/user/pay/v1/query_payment_config", methods=["GET"], view_func=pay.querypaymentconfig)
app.add_url_rule("/user/pay/order/v2/create/app_product", methods=["POST"], view_func=pay.createappproduct)
app.add_url_rule("/user/pay/order/v1/create/app_product/alipay", methods=["POST"], view_func=pay.alipay)
app.add_url_rule("/user/pay/order/v1/create/app_product/wechat", methods=["POST"], view_func=pay.wechat)
app.add_url_rule("/pay/order/v1/check", methods=["POST"], view_func=pay.check)
app.add_url_rule("/pay/order/v1/state", methods=["GET"], view_func=pay.state)

app.add_url_rule("/quest/battleStart", methods = ["POST"], view_func = quest.questBattleStart)
app.add_url_rule("/quest/battleFinish", methods = ["POST"], view_func = quest.questBattleFinish)
app.add_url_rule("/quest/saveBattleReplay", methods = ["POST"], view_func = quest.questSaveBattleReplay)
app.add_url_rule("/quest/getBattleReplay", methods = ["POST"], view_func = quest.questGetBattleReplay)
app.add_url_rule("/quest/changeSquadName", methods = ["POST"], view_func = quest.questChangeSquadName)
app.add_url_rule("/quest/squadFormation", methods = ["POST"], view_func = quest.questSquadFormation)
app.add_url_rule("/quest/getAssistList", methods = ["POST"], view_func = quest.questGetAssistList)
app.add_url_rule("/quest/battleContinue", methods = ["POST"], view_func = quest.questBattleContinue)
app.add_url_rule("/storyreview/markStoryAcceKnown", methods = ["POST"], view_func = quest.markStoryAcceKnown)
app.add_url_rule("/storyreview/readStory", methods = ["POST"], view_func = quest.readStory)
app.add_url_rule("/car/confirmBattleCar", methods = ["POST"], view_func = quest.confirmBattleCar)
app.add_url_rule("/templateTrap/setTrapSquad", methods = ["POST"], view_func = quest.setTrapSquad)
app.add_url_rule("/act25side/battleStart", methods = ["POST"], view_func = quest.questBattleStart)
app.add_url_rule("/act25side/battleFinish", methods = ["POST"], view_func = quest.questBattleFinish)
app.add_url_rule("/retro/typeAct20side/competitionStart", methods = ["POST"], view_func = quest.typeAct20side_competitionStart)
app.add_url_rule("/retro/typeAct20side/competitionFinish", methods = ["POST"], view_func = quest.typeAct20side_competitionFinish)

app.add_url_rule("/mission/confirmMission", methods = ["POST"], view_func = mission.mission_manger().ConfirmMission)
app.add_url_rule("/mission/autoConfirmMissions", methods = ["POST"], view_func = mission.mission_manger().AutoConfirmMissions)

app.add_url_rule("/actcheckinvs/sign", methods = ["POST"], view_func = activity.CheckInReward().sign)
app.add_url_rule("/activity/actCheckinAccess/getCheckInReward", methods = ["POST"], view_func = activity.CheckInReward().getCheckInReward)
app.add_url_rule("/activity/getActivityCheckInReward", methods = ["POST"], view_func = activity.CheckInReward().getActivityCheckInReward)
app.add_url_rule("/activity/prayOnly/getReward", methods = ["POST"], view_func = activity.CheckInReward().getReward)
app.add_url_rule("/activity/enemyDuel/singleBattleStart", methods = ["POST"], view_func = quest.singleBattleStart)
app.add_url_rule("/activity/enemyDuel/singleBattleFinish", methods = ["POST"], view_func = quest.singleBattleFinish)
app.add_url_rule("/activity/act24side/battleStart", methods = ["POST"], view_func = quest.questBattleStart)
app.add_url_rule("/activity/act24side/battleFinish", methods = ["POST"], view_func = quest.questBattleFinish)
app.add_url_rule("/activity/act24side/setTool", methods = ["POST"], view_func = quest.setTool)
app.add_url_rule("/activity/bossRush/battleStart", methods = ["POST"], view_func = quest.questBattleStart)
app.add_url_rule("/activity/bossRush/battleFinish", methods = ["POST"], view_func = quest.questBattleFinish)
app.add_url_rule("/activity/bossRush/relicSelect", methods = ["POST"], view_func = quest.relicSelect)
app.add_url_rule("/activity/act35side/create", methods = ["POST"], view_func = activity.act35side().act35sideCreate)
app.add_url_rule("/activity/act35side/settle", methods = ["POST"], view_func = activity.act35side().act35sidesettle)
app.add_url_rule("/activity/act35side/toBuy", methods = ["POST"], view_func = activity.act35side().act35sideToBuy)
app.add_url_rule("/activity/act35side/refreshShop", methods = ["POST"], view_func = activity.act35side().act35siderefreshShop)
app.add_url_rule("/activity/act35side/buySlot", methods = ["POST"], view_func = activity.act35side().act35sidebuySlot)
app.add_url_rule("/activity/act35side/buyCard", methods = ["POST"], view_func = activity.act35side().act35sidebuyCard)
app.add_url_rule("/activity/act35side/toProcess", methods = ["POST"], view_func = activity.act35side().act35sidetoProcess)
app.add_url_rule("/activity/act35side/process", methods = ["POST"], view_func = activity.act35side().act35sideprocess)
app.add_url_rule("/activity/act35side/nextRound", methods = ["POST"], view_func = activity.act35side().act35nextRound)

app.add_url_rule("/aprilFool/act5fun/battleStart", methods = ["POST"], view_func = quest.questBattleStart)
app.add_url_rule("/aprilFool/act5fun/battleFinish", methods = ["POST"], view_func = quest.act5fun_questBattleFinish)

app.add_url_rule("/rlv2/giveUpGame", methods = ["POST"], view_func = rlv2.rlv2GiveUpGame)
app.add_url_rule("/rlv2/createGame", methods = ["POST"], view_func = rlv2.rlv2CreateGame)
app.add_url_rule("/rlv2/chooseInitialRelic", methods = ["POST"], view_func = rlv2.rlv2ChooseInitialRelic)
app.add_url_rule("/rlv2/selectChoice", methods = ["POST"], view_func = rlv2.rlv2SelectChoice)
app.add_url_rule("/rlv2/chooseInitialRecruitSet", methods = ["POST"], view_func = rlv2.rlv2ChooseInitialRecruitSet)
app.add_url_rule("/rlv2/activeRecruitTicket", methods = ["POST"], view_func = rlv2.rlv2ActiveRecruitTicket)
app.add_url_rule("/rlv2/recruitChar", methods = ["POST"], view_func = rlv2.rlv2RecruitChar)
app.add_url_rule("/rlv2/closeRecruitTicket", methods = ["POST"], view_func = rlv2.rlv2CloseRecruitTicket)
app.add_url_rule("/rlv2/finishEvent", methods = ["POST"], view_func = rlv2.rlv2FinishEvent)
app.add_url_rule("/rlv2/moveAndBattleStart", methods = ["POST"], view_func = rlv2.rlv2MoveAndBattleStart)
app.add_url_rule("/rlv2/battleFinish", methods = ["POST"], view_func = rlv2.rlv2BattleFinish)
app.add_url_rule("/rlv2/finishBattleReward", methods = ["POST"], view_func = rlv2.rlv2FinishBattleReward)
app.add_url_rule("/rlv2/moveTo", methods = ["POST"], view_func = rlv2.rlv2MoveTo)
app.add_url_rule("/rlv2/buyGoods", methods = ["POST"], view_func = rlv2.rlv2BuyGoods)
app.add_url_rule("/rlv2/leaveShop", methods = ["POST"], view_func = rlv2.rlv2LeaveShop)
app.add_url_rule("/rlv2/chooseBattleReward", methods = ["POST"], view_func = rlv2.rlv2ChooseBattleReward)
app.add_url_rule("/rlv2/shopAction", methods = ["POST"], view_func = rlv2.rlv2shopAction)
app.add_url_rule("/rlv2/copper/redraw", methods = ["POST"], view_func = rlv2.rlv2CopperRedraw)

app.add_url_rule("/shop/getGoodPurchaseState", methods=["POST"], view_func=shop.getGoodPurchaseState)
app.add_url_rule("/shop/get<string:shop_type>GoodList", methods=["POST"], view_func=shop.getShopGoodList)
app.add_url_rule("/shop/buySkinGood", methods=["POST"], view_func=shop.buySkinGood)
app.add_url_rule("/shop/buyLowGood", methods=["POST"], view_func=shop.buyLowGood)
app.add_url_rule("/shop/buyHighGood", methods=["POST"], view_func=shop.buyHighGood)
app.add_url_rule("/shop/buyExtraGood", methods=["POST"], view_func=shop.buyExtraGood)
app.add_url_rule("/shop/buyClassicGood", methods=["POST"], view_func=shop.buyClassicGood)
app.add_url_rule("/shop/buyFurniGood", methods=["POST"], view_func=shop.buyFurniGood)
app.add_url_rule("/shop/buyFurniGroup", methods=["POST"], view_func=shop.buyFurniGroup)

app.add_url_rule("/templateShop/getGoodList", methods = ["POST"], view_func = templateShop.getGoodList)
app.add_url_rule("/templateShop/BuyGood", methods = ["POST"], view_func = templateShop.buyGood)

app.add_url_rule("/story/finishStory", methods = ["POST"], view_func = story.storyFinishStory)
app.add_url_rule("/quest/finishStoryStage", methods = ["POST"], view_func = story.storyFinishStory)

app.add_url_rule("/user/bindBirthday", methods = ["POST"], view_func = user.bindBirthday)
app.add_url_rule("/user/auth", methods = ["POST"], view_func = user.Auth)
app.add_url_rule("/user/agreement", methods = ["GET"], view_func = user.Agreement)
app.add_url_rule("/user/checkIn", methods = ["POST"], view_func = user.CheckIn)
app.add_url_rule("/user/changeSecretary", methods = ["POST"], view_func = user.ChangeSecretary)
app.add_url_rule("/user/login", methods = ["POST"], view_func = user.Login)
app.add_url_rule("/user/changeAvatar", methods = ["POST"], view_func = user.ChangeAvatar)
app.add_url_rule("/user/oauth2/v1/grant", methods = ["POST"], view_func = user.OAuth2V1Grant)
app.add_url_rule("/user/info/v1/need_cloud_auth", methods = ["POST"], view_func = user.V1NeedCloudAuth)
app.add_url_rule("/user/yostar_createlogin", methods = ["POST"], view_func = user.YostarCreatelogin)
app.add_url_rule("/u8/user/v1/getToken", methods = ["POST"], view_func = user.V1getToken)
app.add_url_rule("/user/changeResume", methods = ["POST"], view_func = user.changeResume)
app.add_url_rule("/businessCard/changeNameCardComponent", methods = ["POST"], view_func = user.businessCard_changeNameCardComponent)
app.add_url_rule("/businessCard/changeNameCardSkin", methods = ["POST"], view_func = user.businessCard_changeNameCardSkin)
app.add_url_rule("/businessCard/getOtherPlayerNameCard", methods = ["POST"], view_func = user.getOtherPlayerNameCard)
app.add_url_rule("/businessCard/editNameCard", methods = ["POST"], view_func = user.editNameCard)
app.add_url_rule("/user/auth/v1/token_by_phone_password", methods = ["POST"], view_func = user.auth_v1_token_by_phone_password)
app.add_url_rule("/user/auth/v2/token_by_phone_code", methods = ["POST"], view_func = user.auth_v2_token_by_phone_code)
app.add_url_rule("/user/info/v1/basic", methods = ["GET"], view_func = user.info_v1_basic)
app.add_url_rule("/user/oauth2/v2/grant", methods = ["POST"], view_func = user.oauth2_v2_grant)
app.add_url_rule("/app/v1/config", methods = ["GET"], view_func = user.app_v1_config)
app.add_url_rule("/general/v1/server_time", methods = ["GET"], view_func = user.general_v1_server_time)
app.add_url_rule("/general/v1/send_phone_code", methods = ["POST"], view_func = user.userSend_phone_code)
app.add_url_rule("/u8/user/auth/v1/agreement_version", methods = ["GET"], view_func = user.agreement_version)

app.add_url_rule("/sandboxPerm/sandboxV2/createGame", methods = ["POST"], view_func = sandbox.createGame)
app.add_url_rule("/sandboxPerm/sandboxV2/battleStart", methods = ["POST"], view_func = sandbox.battleStart)
app.add_url_rule("/sandboxPerm/sandboxV2/battleFinish", methods = ["POST"], view_func = sandbox.battleFinish)
app.add_url_rule("/sandboxPerm/sandboxV2/settleGame", methods = ["POST"], view_func = sandbox.settleGame)
app.add_url_rule("/sandboxPerm/sandboxV2/eatFood", methods = ["POST"], view_func = sandbox.eatFood)
app.add_url_rule("/sandboxPerm/sandboxV2/setSquad", methods = ["POST"], view_func = sandbox.setSquad)
app.add_url_rule("/sandboxPerm/sandboxV2/homeBuildSave", methods = ["POST"], view_func = sandbox.homeBuildSave)
app.add_url_rule("/sandboxPerm/sandboxV2/exploreMode", methods = ["POST"], view_func = sandbox.exploreMode)
app.add_url_rule("/sandboxPerm/sandboxV2/eventChoice", methods=["POST"], view_func = sandbox.eventChoice)
app.add_url_rule("/sandboxPerm/sandboxV2/monthBattleStart", methods = ["POST"], view_func = sandbox.monthBattleStart)
app.add_url_rule("/sandboxPerm/sandboxV2/monthBattleFinish", methods = ["POST"], view_func = sandbox.monthBattleFinish)

app.add_url_rule("/gacha/normalGacha", methods = ["POST"], view_func = gacha.normalGacha)
app.add_url_rule("/gacha/boostNormalGacha", methods = ["POST"], view_func = gacha.boostNormalGacha)
app.add_url_rule("/gacha/finishNormalGacha", methods = ["POST"], view_func = gacha.finishNormalGacha)
app.add_url_rule("/gacha/syncNormalGacha", methods = ["POST"], view_func = gacha.syncNormalGacha)
app.add_url_rule("/gacha/getPoolDetail", methods = ["POST"], view_func = gacha.getPoolDetail)
app.add_url_rule("/gacha/advancedGacha", methods = ["POST"], view_func = gacha.advancedGacha)
app.add_url_rule("/gacha/tenAdvancedGacha", methods = ["POST"], view_func = gacha.tenAdvancedGacha)
app.add_url_rule("/gacha/choosePoolUp", methods=["POST"], view_func=gacha.choosePoolUp)
app.add_url_rule("/gacha", methods = ["GET"], view_func = gacha.gacha)
app.add_url_rule("/api/gacha/cate", methods = ["GET"], view_func = gacha.cate)
app.add_url_rule("/api/is/rogue_1/bulletinVersion", methods = ["GET"], view_func = gacha.bulletinVersion)
app.add_url_rule("/api/gacha/history", methods = ["GET"], view_func = gacha.history)

app.add_url_rule('/social/setAssistCharList', methods=['POST'], view_func=social.setAssistCharList)
app.add_url_rule('/social/getSortListInfo', methods=['POST'], view_func=social.getSortListInfo)
app.add_url_rule('/social/getFriendList', methods=['POST'], view_func=social.getFriendList)
app.add_url_rule('/social/getFriendRequestList', methods=['POST'], view_func=social.getFriendRequestList)
app.add_url_rule('/social/processFriendRequest', methods=['POST'], view_func=social.processFriendRequest)
app.add_url_rule('/social/sendFriendRequest', methods=['POST'], view_func=social.sendFriendRequest)
app.add_url_rule('/social/setFriendAlias', methods=['POST'], view_func=social.setFriendAlias)
app.add_url_rule('/social/deleteFriend', methods=['POST'], view_func=social.deleteFriend)
app.add_url_rule('/social/searchPlayer', methods=['POST'], view_func=social.searchPlayer)
app.add_url_rule("/social/setCardShowMedal", methods = ["POST"], view_func = social.setCardShowMedal)

# app.add_url_rule("/iedsafe/Client/android/19791/config2.xml", methods = ["GET"], view_func = other.anticheat)
# app.add_url_rule("/event", methods = ["POST"], view_func = other.event)
# app.add_url_rule("/batch_event", methods = ["POST"], view_func = other.batch_event)
# app.add_url_rule("/beat", methods = ["POST"], view_func = other.beat)

app.add_url_rule("/charRotation/setCurrent", methods = ["POST"], view_func = charrotation.setCurrent)
app.add_url_rule("/charRotation/createPreset", methods = ["POST"], view_func = charrotation.createPreset)
app.add_url_rule("/charRotation/deletePreset", methods = ["POST"], view_func = charrotation.deletePreset)
app.add_url_rule("/charRotation/updatePreset", methods = ["POST"], view_func = charrotation.updatePreset)

app.add_url_rule("/vecBreakV2/getSeasonRecord", methods = ["POST"], view_func = vecbreak.getSeasonRecord)
app.add_url_rule("/activity/rewardAllMilestone", methods = ["POST"], view_func = vecbreak.rewardAllMilestone)
app.add_url_rule("/activity/rewardMilestone", methods = ["POST"], view_func = vecbreak.rewardMilestone)
app.add_url_rule("/activity/vecBreakV2/changeBuffList", methods = ["POST"], view_func = vecbreak.vecV2changeBuffList)
app.add_url_rule("/activity/vecBreakV2/defendBattleStart", methods = ["POST"], view_func = vecbreak.defendBattleStart)
app.add_url_rule("/activity/vecBreakV2/defendBattleFinish", methods = ["POST"], view_func = vecbreak.defendBattleFinish)
app.add_url_rule("/activity/vecBreakV2/setDefend", methods = ["POST"], view_func = vecbreak.setDefend)
app.add_url_rule("/activity/vecBreakV2/battleStart", methods = ["POST"], view_func = vecbreak.vecV2BattleStart)
app.add_url_rule("/activity/vecBreakV2/battleFinish", methods = ["POST"], view_func = vecbreak.vecV2battleFinish)

app.add_url_rule('/recalRune/battleStart', methods=['POST'], view_func=crisis.recalRune_battleStart)
app.add_url_rule('/recalRune/battleFinish', methods=['POST'], view_func=crisis.recalRune_battleFinish)


# 启动逻辑适配
def writeLog(data):
    print(f'[{datetime.now()}] {data}')

if __name__ == "__main__":
    start_global_event_loop()
    if useMemoryCache:
        writeLog('Loading all table data to memory')
        preload_json_data()
        writeLog('Sucessfully loaded all table data')
    
    writeLog(f'[SERVER] Server started at http://{host}:{port} using {"FastAPI" if use_fastapi else "Flask"}')
    
    if use_fastapi:
        import uvicorn
        uvicorn.run(app, host=host, port=port)
    else:
        app.run(host=host, port=port, debug=True)

