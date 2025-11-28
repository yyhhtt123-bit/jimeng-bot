import logging
import json
import time
import asyncio
import os  # 新增：用于读取环境变量
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from volcengine.visual.VisualService import VisualService

# ================= 配置区域 (改为读取环境变量) =================
# 如果本地运行找不到环境变量，会报错，这是正常的安全机制
VOLC_AK = os.environ.get("VOLC_AK")
VOLC_SK = os.environ.get("VOLC_SK")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
# =========================================================

# 检查配置是否读取成功
if not all([VOLC_AK, VOLC_SK, TG_BOT_TOKEN]):
    print("错误：未检测到环境变量！请在部署平台设置 VOLC_AK, VOLC_SK 和 TG_BOT_TOKEN")
    exit(1)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

visual_service = VisualService()
visual_service.set_ak(VOLC_AK)
visual_service.set_sk(VOLC_SK)

def jimeng_generate_sync(prompt):
    try:
        submit_form = {
            "req_key": "jimeng_t2i_v40",
            "prompt": prompt,
            "scale": 0.5,
            "force_single": True
        }
        submit_resp = visual_service.cv_sync2async_submit_task(submit_form)
        
        if 'data' not in submit_resp or 'task_id' not in submit_resp['data']:
            return {"success": False, "msg": f"提交失败: {submit_resp}"}
            
        task_id = submit_resp['data']['task_id']
        logging.info(f"Task Submitted: {task_id}")

        for _ in range(30): 
            query_form = {"req_key": "jimeng_t2i_v40", "task_id": task_id}
            query_resp = visual_service.cv_sync2async_get_result(query_form)
            status = query_resp.get('status')
            
            if status == 10000:
                if 'data' in query_resp and 'resp_data' in query_resp['data']:
                    result_data = json.loads(query_resp['data']['resp_data'])
                    if 'image_urls' in result_data and len(result_data['image_urls']) > 0:
                        return {"success": True, "url": result_data['image_urls'][0]}
                return {"success": False, "msg": "生成成功但未找到图片链接"}
            elif status == 10001:
                time.sleep(2)
                continue
            else:
                return {"success": False, "msg": f"API错误: {query_resp.get('message')}"}
                
        return {"success": False, "msg": "生成超时"}
    except Exception as e:
        return {"success": False, "msg": f"异常: {str(e)}"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好！即梦AI机器人已就绪。\n发送 /gen <提示词> 开始绘图。")

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("请提供提示词，例如: /gen 森林里的城堡")
        return

    prompt = ' '.join(context.args)
    processing_msg = await update.message.reply_text(f"🎨 正在绘制: 「{prompt}」\n请稍候...")
    
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, jimeng_generate_sync, prompt)

    if result["success"]:
        # 删除之前的“正在绘制”消息（可选，或者直接编辑）
        await processing_msg.delete() 
        await update.message.reply_photo(photo=result["url"], caption=f"Prompt: {prompt}")
    else:
        await processing_msg.edit_text(f"❌ 失败: {result['msg']}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen", generate_image))
    print("Bot is running...")
    application.run_polling()