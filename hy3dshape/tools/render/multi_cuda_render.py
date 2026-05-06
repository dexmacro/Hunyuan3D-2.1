import os  
import subprocess  
import glob
import types
import os
from concurrent.futures import ProcessPoolExecutor
import shutil
import shlex
def run_render_subprocess(args_dict, timeout=None):
  """
  用 subprocess 方式启动一个独立的 render.py 进程
  返回 (returncode, stdout, stderr, success)
  """
  cmd_parts = ["python", "hy3dshape/tools/render/render.py]
  for k, v in args_dict.items():
    if v is None:
      continue
    if isinstance(v, bool):
      if v:
        cmd_parts.append(f"--{k}")
      continue
    cmd_parts.append(f"--{k}")
    cmd_parts.append(str(v))
  cmd_str = " ".join(shlex.quote(x) for x in cmd_parts)
  print(f"启动: {cmd_str}")
  try:
    result = subprocess.run(cmd_parts,capture_output=True,text=True,check=False,timeout=timeout)
    success = result.returncode == 0
    return {"success": success,"returncode": result.returncode,"stdout": result.stdout.strip(),"stderr": result.stderr.strip(),"src": args_dict.get("object", "unknown"),"dst": args_dict.get("output_folder", "unknown")}
  except subprocess.TimeoutExpired:
    return {"success": False,"returncode": -1,"stdout": "","stderr": "Timeout expired","src": args_dict.get("object", "unknown"),"dst": args_dict.get("output_folder", "unknown")}
  except Exception as e:
    return {"success": False,"returncode": -999,"stdout": "","stderr": str(e),"src": args_dict.get("object", "unknown"),"dst": args_dict.get("output_folder", "unknown")}

if __name__ == "__main__":
  INPUT_DIR = "path/to/stls/inputs"
  BASE_OUTPUT_DIR = "path/to/stls/outputs"
  model_files = glob.glob(os.path.join(INPUT_DIR, "*.obj"))
  configs = []
  for item in model_files:
    model_name = os.path.splitext(os.path.basename(item))[0]
    output_folder = os.path.join(BASE_OUTPUT_DIR, model_name)
    config = {
      "views": 24,              #随机视角数量
      "resolution": 512,        # 渲染分辨率
      "engine": 'CYCLES',       # 渲染引擎 (CYCLES 或 BLENDER_EEVEE)
      "geo_mode": True,         # 是否开启几何模式（开启后会进行球面随机采样）
      "save_depth": False,       # 是否保存深度图 
      "save_normal": False,      # 是否保存法线图
      "save_albedo": False,     # 是否保存反照率图
      "save_mr": False,         # 是否保存金属/粗糙度图  
      "save_mist": False,       # 是否保存薄雾图
      "split_normal": False,     # 是否拆分法线
      "save_mesh": False,         # 是否导出处理后的网格(.ply)  
      "object": item,
      "output_folder": output_folder
    }
    configs.append(config)
  with ProcessPoolExecutor(max_workers=3) as executor:
    future_to_src = {executor.submit(run_render_subprocess, cfg): cfg for cfg in configs}
    for future in as_completed(future_to_src):
      src = future_to_src[future]
      try:
        result = future.result()
      except Exception as e:
        print(f" 提交失败: {e}")
    
