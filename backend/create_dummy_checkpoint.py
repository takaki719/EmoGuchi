"""
開発用のダミーチェックポイントファイルを作成
実際のkushinada-hubert-largeモデルがない場合のテスト用
"""

import torch
import os

def create_dummy_checkpoint():
    """ダミーのチェックポイントファイルを作成"""
    
    # ダミーのモデル重み（実際のHubertの次元に近い値）
    hidden_dim = 1024  # Hubert Largeの隠れ層次元
    num_classes = 4    # 4感情クラス
    projector_dim = 256  # Projectorの中間次元
    
    dummy_weights = {
        "Downstream": {
            # Projector layer
            "projector.weight": torch.randn(projector_dim, hidden_dim),
            "projector.bias": torch.randn(projector_dim),
            
            # Post-net layer  
            "model.post_net.linear.weight": torch.randn(num_classes, projector_dim),
            "model.post_net.linear.bias": torch.randn(num_classes),
        }
    }
    
    # チェックポイントファイルの保存
    ckpt_path = "./ckpt/dev-best.ckpt"
    os.makedirs(os.path.dirname(ckpt_path), exist_ok=True)
    
    torch.save(dummy_weights, ckpt_path)
    print(f"✅ ダミーチェックポイントファイルを作成しました: {ckpt_path}")
    
    # ファイル情報表示
    file_size = os.path.getsize(ckpt_path)
    print(f"📁 ファイルサイズ: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")

if __name__ == "__main__":
    create_dummy_checkpoint()