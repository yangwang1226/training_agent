"""
维度生成服务
根据角色信息动态生成能力评估维度
"""
import json
import logging
from typing import Optional, List, Dict, Any

from .dimension_models import DimensionConfig, SceneDimensionConfig, DimensionGenerationResult

logger = logging.getLogger(__name__)


DIMENSION_GENERATION_PROMPT = """你是一位培训评估专家，需要根据培训场景设计能力评估维度。

## 场景信息
- 行业：{industry}
- AI模拟角色：{role_type}
- 角色描述：{role_description}
- 培训目标：{training_goal}

## 任务
设计5个核心能力评估维度，要求：
1. 维度名称简洁明确（2-4个字）
2. 每个维度包含3-5个评估子项
3. 权重分配合理（总和为1.0，每个维度权重在0.1-0.35之间）
4. 维度应针对被培训人员的能力评估，而非AI模拟的角色

## 输出格式（严格JSON，不要包含markdown代码块标记）
{{
  "dimensions": [
    {{
      "dimension_name": "维度名称",
      "weight": 0.20,
      "sub_criteria": {{
        "子项1": "评估标准描述",
        "子项2": "评估标准描述"
      }},
      "score_levels": {{
        "优秀": "90-100分的表现描述",
        "良好": "75-89分的表现描述",
        "及格": "60-74分的表现描述",
        "不及格": "0-59分的表现描述"
      }}
    }}
  ],
  "design_rationale": "维度设计理由"
}}
"""


SALES_DIMENSIONS = [
    {
        "dimension_name": "沟通技巧",
        "weight": 0.20,
        "sub_criteria": {
            "表达清晰": "语言表达是否清晰、有条理",
            "语速适中": "语速是否合适，不快不慢",
            "礼貌用语": "是否使用礼貌用语，态度友好",
            "倾听能力": "是否认真倾听客户，不打断"
        },
        "score_levels": {
            "优秀": "表达专业流畅，极具感染力",
            "良好": "表达清晰，沟通顺畅",
            "及格": "基本清晰，偶有瑕疵",
            "不及格": "表达混乱，难以理解"
        }
    },
    {
        "dimension_name": "产品知识",
        "weight": 0.20,
        "sub_criteria": {
            "特点介绍": "产品特点介绍是否准确",
            "优势对比": "与竞品对比是否清晰",
            "参数回答": "技术参数回答是否正确",
            "案例引用": "是否引用成功案例"
        },
        "score_levels": {
            "优秀": "产品专家级别，信手拈来",
            "良好": "熟悉产品，能回答大部分问题",
            "及格": "基本了解，但不够深入",
            "不及格": "产品知识匮乏，频繁卡壳"
        }
    },
    {
        "dimension_name": "需求挖掘",
        "weight": 0.20,
        "sub_criteria": {
            "提问技巧": "提问是否有针对性",
            "信息收集": "收集的信息是否完整",
            "痛点识别": "是否识别客户痛点",
            "需求确认": "是否确认理解客户需求"
        },
        "score_levels": {
            "优秀": "深度挖掘，精准把握需求",
            "良好": "善于提问，收集信息完整",
            "及格": "有挖掘意识，但不够深入",
            "不及格": "被动回答，缺乏挖掘"
        }
    },
    {
        "dimension_name": "异议处理",
        "weight": 0.20,
        "sub_criteria": {
            "价格异议": "价格异议处理是否得当",
            "竞品对比": "竞品对比应对是否有效",
            "信任建立": "是否建立客户信任",
            "顾虑消除": "是否消除客户顾虑"
        },
        "score_levels": {
            "优秀": "从容应对，化异议为机会",
            "良好": "处理得当，客户接受度高",
            "及格": "基本处理，但不够巧妙",
            "不及格": "回避异议或处理不当"
        }
    },
    {
        "dimension_name": "促成技巧",
        "weight": 0.20,
        "sub_criteria": {
            "时机把握": "促单时机把握是否准确",
            "话术运用": "促单话术是否恰当",
            "紧迫感": "是否营造紧迫感",
            "成交引导": "是否引导客户成交"
        },
        "score_levels": {
            "优秀": "精准把握，高效成交",
            "良好": "善于促单，成交率高",
            "及格": "有促单意识，但时机欠佳",
            "不及格": "缺乏促单技巧，错失机会"
        }
    }
]


CUSTOMER_SERVICE_DIMENSIONS = [
    {
        "dimension_name": "服务态度",
        "weight": 0.25,
        "sub_criteria": {
            "礼貌用语": "是否使用礼貌用语，态度友好",
            "耐心程度": "是否耐心解答客户问题",
            "情绪控制": "面对困难客户是否能保持冷静",
            "主动关怀": "是否主动关心客户需求"
        },
        "score_levels": {
            "优秀": "服务热情周到，客户如沐春风",
            "良好": "态度友好，服务到位",
            "及格": "态度尚可，偶有急躁",
            "不及格": "态度冷淡，缺乏耐心"
        }
    },
    {
        "dimension_name": "问题解决",
        "weight": 0.30,
        "sub_criteria": {
            "问题理解": "是否准确理解客户问题",
            "解决方案": "提供的解决方案是否有效",
            "跟进处理": "是否做好问题跟进",
            "知识运用": "是否正确运用业务知识"
        },
        "score_levels": {
            "优秀": "快速精准解决问题，超出预期",
            "良好": "能有效解决问题，客户满意",
            "及格": "基本解决问题，效率一般",
            "不及格": "问题解决不力，客户不满"
        }
    },
    {
        "dimension_name": "沟通表达",
        "weight": 0.20,
        "sub_criteria": {
            "表达清晰": "语言表达是否清晰易懂",
            "倾听能力": "是否认真倾听客户诉求",
            "确认反馈": "是否确认客户理解",
            "信息传递": "信息传递是否准确完整"
        },
        "score_levels": {
            "优秀": "表达精准，沟通高效",
            "良好": "表达清晰，沟通顺畅",
            "及格": "基本表达清楚，偶有歧义",
            "不及格": "表达不清，沟通困难"
        }
    },
    {
        "dimension_name": "业务知识",
        "weight": 0.15,
        "sub_criteria": {
            "政策掌握": "是否熟悉相关政策和规定",
            "流程熟悉": "是否熟悉业务流程",
            "系统操作": "是否能熟练操作系统"
        },
        "score_levels": {
            "优秀": "业务精通，对答如流",
            "良好": "熟悉业务，能处理常见问题",
            "及格": "了解基本业务，需查阅资料",
            "不及格": "业务知识薄弱，频繁出错"
        }
    },
    {
        "dimension_name": "应变能力",
        "weight": 0.10,
        "sub_criteria": {
            "突发处理": "处理突发情况的能力",
            "灵活变通": "是否能灵活应对各种情况"
        },
        "score_levels": {
            "优秀": "应对自如，化险为夷",
            "良好": "能妥善处理突发情况",
            "及格": "基本能应对，略显被动",
            "不及格": "应变能力差，手足无措"
        }
    }
]


TEACHER_DIMENSIONS = [
    {
        "dimension_name": "教学能力",
        "weight": 0.25,
        "sub_criteria": {
            "知识讲解": "知识点讲解是否清晰",
            "教学方法": "教学方法是否得当",
            "课堂掌控": "课堂节奏把控能力",
            "因材施教": "是否能针对不同学生调整"
        },
        "score_levels": {
            "优秀": "教学精湛，深入浅出",
            "良好": "教学得法，学生易懂",
            "及格": "能完成教学，方法一般",
            "不及格": "教学混乱，学生困惑"
        }
    },
    {
        "dimension_name": "沟通技巧",
        "weight": 0.20,
        "sub_criteria": {
            "表达清晰": "语言表达是否清晰",
            "倾听理解": "是否倾听学生和家长诉求",
            "反馈及时": "反馈是否及时有效",
            "情绪管理": "情绪管理能力"
        },
        "score_levels": {
            "优秀": "沟通顺畅，亲和力强",
            "良好": "沟通良好，关系融洽",
            "及格": "基本能沟通，偶有障碍",
            "不及格": "沟通困难，关系紧张"
        }
    },
    {
        "dimension_name": "专业知识",
        "weight": 0.20,
        "sub_criteria": {
            "学科知识": "学科专业知识掌握程度",
            "教育理论": "教育理论知识运用",
            "前沿了解": "了解学科前沿动态"
        },
        "score_levels": {
            "优秀": "学识渊博，见解独到",
            "良好": "知识扎实，能答疑解惑",
            "及格": "掌握基本知识，偶有盲区",
            "不及格": "知识薄弱，难以胜任"
        }
    },
    {
        "dimension_name": "学生管理",
        "weight": 0.20,
        "sub_criteria": {
            "问题识别": "是否能识别学生问题",
            "心理疏导": "心理疏导能力",
            "行为引导": "行为引导能力",
            "家校沟通": "家校沟通能力"
        },
        "score_levels": {
            "优秀": "善于发现问题，引导有方",
            "良好": "能关注学生，管理得当",
            "及格": "有管理意识，方法欠佳",
            "不及格": "忽视学生问题，管理混乱"
        }
    },
    {
        "dimension_name": "职业素养",
        "weight": 0.15,
        "sub_criteria": {
            "师德师风": "师德师风表现",
            "责任心": "工作责任心",
            "持续学习": "自我提升意识"
        },
        "score_levels": {
            "优秀": "师德高尚，敬业奉献",
            "良好": "为人师表，尽职尽责",
            "及格": "基本符合教师规范",
            "不及格": "师德有亏，责任心差"
        }
    }
]


SECURITY_DIMENSIONS = [
    {
        "dimension_name": "安全意识",
        "weight": 0.25,
        "sub_criteria": {
            "隐患识别": "是否能识别安全隐患",
            "风险预判": "风险预判能力",
            "防范意识": "安全防范意识"
        },
        "score_levels": {
            "优秀": "安全意识极强，防患未然",
            "良好": "安全意识强，能发现隐患",
            "及格": "有安全意识，偶有疏忽",
            "不及格": "安全意识薄弱"
        }
    },
    {
        "dimension_name": "应急处置",
        "weight": 0.25,
        "sub_criteria": {
            "反应速度": "应急反应速度",
            "处置规范": "处置流程是否规范",
            "协调能力": "协调各方资源能力"
        },
        "score_levels": {
            "优秀": "反应迅速，处置得当",
            "良好": "能及时有效处理",
            "及格": "基本能应对，效率一般",
            "不及格": "反应迟钝，处置混乱"
        }
    },
    {
        "dimension_name": "服务态度",
        "weight": 0.20,
        "sub_criteria": {
            "礼貌待人": "是否礼貌待人",
            "耐心解答": "是否耐心解答疑问",
            "主动服务": "主动服务意识"
        },
        "score_levels": {
            "优秀": "服务热情，形象良好",
            "良好": "态度友好，服务到位",
            "及格": "态度尚可，服务一般",
            "不及格": "态度生硬，服务差"
        }
    },
    {
        "dimension_name": "业务技能",
        "weight": 0.15,
        "sub_criteria": {
            "设备操作": "安防设备操作能力",
            "巡逻规范": "巡逻工作规范性",
            "记录完整": "工作记录是否完整"
        },
        "score_levels": {
            "优秀": "技能娴熟，操作规范",
            "良好": "技能熟练，操作正确",
            "及格": "基本掌握，偶有失误",
            "不及格": "技能生疏，操作不当"
        }
    },
    {
        "dimension_name": "沟通协作",
        "weight": 0.15,
        "sub_criteria": {
            "汇报沟通": "与上级沟通汇报",
            "团队协作": "与同事协作配合",
            "群众沟通": "与群众沟通能力"
        },
        "score_levels": {
            "优秀": "沟通顺畅，协作默契",
            "良好": "沟通良好，配合到位",
            "及格": "基本能沟通协作",
            "不及格": "沟通不畅，协作困难"
        }
    }
]


PSYCHOLOGIST_DIMENSIONS = [
    {
        "dimension_name": "共情能力",
        "weight": 0.25,
        "sub_criteria": {
            "情感理解": "是否能理解来访者情感",
            "情感回应": "情感回应是否恰当",
            "无条件接纳": "是否能无条件接纳来访者"
        },
        "score_levels": {
            "优秀": "共情深刻，来访者感到被理解",
            "良好": "能准确共情，回应得当",
            "及格": "有共情意识，偶有偏差",
            "不及格": "缺乏共情，来访者感到被忽视"
        }
    },
    {
        "dimension_name": "咨询技术",
        "weight": 0.25,
        "sub_criteria": {
            "倾听技术": "倾听技术运用",
            "提问技术": "提问技术运用",
            "反馈技术": "反馈技术运用",
            "干预技术": "干预技术运用"
        },
        "score_levels": {
            "优秀": "技术娴熟，运用自如",
            "良好": "技术运用得当，效果明显",
            "及格": "基本掌握，运用生硬",
            "不及格": "技术欠缺，难以推进"
        }
    },
    {
        "dimension_name": "专业素养",
        "weight": 0.20,
        "sub_criteria": {
            "理论知识": "心理学理论知识",
            "伦理守则": "是否遵守伦理守则",
            "边界意识": "职业边界意识"
        },
        "score_levels": {
            "优秀": "专业深厚，伦理严谨",
            "良好": "专业扎实，遵守伦理",
            "及格": "基本专业，偶有疏漏",
            "不及格": "专业薄弱，伦理有亏"
        }
    },
    {
        "dimension_name": "沟通表达",
        "weight": 0.15,
        "sub_criteria": {
            "语言表达": "语言表达是否清晰温和",
            "非语言沟通": "非语言沟通运用",
            "氛围营造": "是否能营造安全氛围"
        },
        "score_levels": {
            "优秀": "表达精准，氛围温暖",
            "良好": "表达清晰，氛围舒适",
            "及格": "基本表达清楚",
            "不及格": "表达不当，氛围紧张"
        }
    },
    {
        "dimension_name": "问题解决",
        "weight": 0.15,
        "sub_criteria": {
            "问题评估": "问题评估是否准确",
            "方案制定": "咨询方案制定",
            "效果评估": "咨询效果评估"
        },
        "score_levels": {
            "优秀": "评估精准，方案有效",
            "良好": "评估准确，方案可行",
            "及格": "基本评估，方案一般",
            "不及格": "评估偏差，方案无效"
        }
    }
]


DEFAULT_DIMENSIONS = [
    {
        "dimension_name": "沟通能力",
        "weight": 0.25,
        "sub_criteria": {
            "表达清晰": "语言表达是否清晰",
            "倾听理解": "是否认真倾听并理解",
            "反馈及时": "反馈是否及时有效"
        },
        "score_levels": {
            "优秀": "沟通顺畅，表达精准",
            "良好": "沟通良好，表达清晰",
            "及格": "基本能沟通",
            "不及格": "沟通困难"
        }
    },
    {
        "dimension_name": "专业知识",
        "weight": 0.25,
        "sub_criteria": {
            "知识掌握": "专业知识掌握程度",
            "知识运用": "是否能运用知识解决问题"
        },
        "score_levels": {
            "优秀": "专业精通",
            "良好": "知识扎实",
            "及格": "基本掌握",
            "不及格": "知识薄弱"
        }
    },
    {
        "dimension_name": "问题解决",
        "weight": 0.20,
        "sub_criteria": {
            "问题识别": "是否能识别问题关键",
            "解决方案": "解决方案是否有效",
            "执行能力": "执行解决方案的能力"
        },
        "score_levels": {
            "优秀": "解决高效，方案完美",
            "良好": "能有效解决问题",
            "及格": "基本能解决",
            "不及格": "解决不力"
        }
    },
    {
        "dimension_name": "服务意识",
        "weight": 0.15,
        "sub_criteria": {
            "主动服务": "是否主动提供服务",
            "态度友好": "服务态度是否友好"
        },
        "score_levels": {
            "优秀": "服务热情周到",
            "良好": "服务态度良好",
            "及格": "服务尚可",
            "不及格": "服务意识差"
        }
    },
    {
        "dimension_name": "应变能力",
        "weight": 0.15,
        "sub_criteria": {
            "反应速度": "对突发情况的反应速度",
            "处理效果": "处理突发情况的效果"
        },
        "score_levels": {
            "优秀": "反应迅速，处理得当",
            "良好": "能及时处理",
            "及格": "基本能应对",
            "不及格": "应变能力差"
        }
    }
]

DEFAULT_TEMPLATES = {
    "sales": SALES_DIMENSIONS,
    "customer_service": CUSTOMER_SERVICE_DIMENSIONS,
    "teacher": TEACHER_DIMENSIONS,
    "security": SECURITY_DIMENSIONS,
    "psychologist": PSYCHOLOGIST_DIMENSIONS,
    "default": DEFAULT_DIMENSIONS
}


class DimensionGenerator:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def generate_dimensions(
        self,
        industry: str,
        role_type: str,
        role_description: str,
        training_goal: str = ""
    ) -> DimensionGenerationResult:
        if not self.llm_client:
            return self._get_fallback_dimensions(industry, role_type)
        
        try:
            prompt = DIMENSION_GENERATION_PROMPT.format(
                industry=industry,
                role_type=role_type,
                role_description=role_description,
                training_goal=training_goal or "提升被培训人员的专业能力"
            )
            
            response = self.llm_client.chat(prompt)
            
            if not response:
                return self._get_fallback_dimensions(industry, role_type)
            
            result = self._parse_llm_response(response)
            
            if result.success:
                return result
            else:
                return self._get_fallback_dimensions(industry, role_type)
                
        except Exception as e:
            logger.error(f"生成维度失败: {str(e)}")
            return self._get_fallback_dimensions(industry, role_type)

    def _parse_llm_response(self, response: str) -> DimensionGenerationResult:
        try:
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            json_str = json_str.strip()
            
            data = json.loads(json_str)
            
            dimensions = []
            for dim_data in data.get("dimensions", []):
                dim = DimensionConfig(
                    dimension_name=dim_data.get("dimension_name", ""),
                    weight=dim_data.get("weight", 0.2),
                    sub_criteria=dim_data.get("sub_criteria", {}),
                    score_levels=dim_data.get("score_levels", {})
                )
                dimensions.append(dim)
            
            if not dimensions:
                return DimensionGenerationResult(
                    success=False,
                    error_message="未解析到有效维度"
                )
            
            self._normalize_weights(dimensions)
            
            return DimensionGenerationResult(
                success=True,
                dimensions=dimensions,
                design_rationale=data.get("design_rationale", "")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            return DimensionGenerationResult(
                success=False,
                error_message=f"JSON解析失败: {str(e)}"
            )
        except Exception as e:
            logger.error(f"解析响应失败: {str(e)}")
            return DimensionGenerationResult(
                success=False,
                error_message=f"解析响应失败: {str(e)}"
            )

    def _normalize_weights(self, dimensions: List[DimensionConfig]):
        total_weight = sum(d.weight for d in dimensions)
        if total_weight > 0 and abs(total_weight - 1.0) > 0.001:
            for dim in dimensions:
                dim.weight = round(dim.weight / total_weight, 2)
            
            current_total = sum(d.weight for d in dimensions)
            if current_total != 1.0:
                dimensions[0].weight += 1.0 - current_total

    def _get_fallback_dimensions(
        self, 
        industry: str, 
        role_type: str
    ) -> DimensionGenerationResult:
        template_key = self._match_template(industry, role_type)
        dimensions_data = DEFAULT_TEMPLATES.get(template_key, DEFAULT_DIMENSIONS)
        
        dimensions = [
            DimensionConfig(
                dimension_name=d.get("dimension_name", ""),
                weight=d.get("weight", 0.2),
                sub_criteria=d.get("sub_criteria", {}),
                score_levels=d.get("score_levels", {})
            )
            for d in dimensions_data
        ]
        
        return DimensionGenerationResult(
            success=True,
            dimensions=dimensions,
            design_rationale=f"使用预设模板: {template_key}"
        )

    def _match_template(self, industry: str, role_type: str) -> str:
        industry_lower = industry.lower() if industry else ""
        role_lower = role_type.lower() if role_type else ""
        
        if any(kw in industry_lower for kw in ["销售", "零售", "汽车", "房产", "保险"]):
            return "sales"
        
        if any(kw in industry_lower for kw in ["客服", "呼叫中心", "服务"]):
            return "customer_service"
        
        if any(kw in industry_lower for kw in ["教育", "培训", "学校"]):
            return "teacher"
        
        if any(kw in role_lower for kw in ["保安", "安保", "安全"]):
            return "security"
        
        if any(kw in industry_lower for kw in ["心理", "咨询"]):
            return "psychologist"
        
        if any(kw in role_lower for kw in ["客户", "顾客", "家长", "学生", "患者"]):
            if "家长" in role_lower or "学生" in role_lower:
                return "teacher"
            return "sales"
        
        return "default"

    def get_template(self, template_name: str) -> List[DimensionConfig]:
        dimensions_data = DEFAULT_TEMPLATES.get(template_name, DEFAULT_DIMENSIONS)
        return [
            DimensionConfig(
                dimension_name=d.get("dimension_name", ""),
                weight=d.get("weight", 0.2),
                sub_criteria=d.get("sub_criteria", {}),
                score_levels=d.get("score_levels", {})
            )
            for d in dimensions_data
        ]

    def list_templates(self) -> List[Dict[str, str]]:
        return [
            {"key": "sales", "name": "销售岗位", "description": "适用于销售、零售等行业"},
            {"key": "customer_service", "name": "客服岗位", "description": "适用于客服、呼叫中心等行业"},
            {"key": "teacher", "name": "教师岗位", "description": "适用于教育、培训等行业"},
            {"key": "security", "name": "安保岗位", "description": "适用于保安、安保等行业"},
            {"key": "psychologist", "name": "心理咨询师", "description": "适用于心理咨询行业"},
            {"key": "default", "name": "通用模板", "description": "适用于其他行业"}
        ]
