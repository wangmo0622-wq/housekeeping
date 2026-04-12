from __future__ import annotations

from typing import Any, Set

from django.core.exceptions import ValidationError

from .models import Category


def validate_category_parent_for_save(
    *,
    parent: Category | None,
    node: Category | None = None,
) -> None:
    """
    创建或调整父级时校验：
    - 若有父级，父级必须是一级分类（parent_id==0）
    - 若当前节点下已有子分类，不能再指定父级（否则子节点会变成三级）
    - 禁止把祖先设为父级等成环
    """
    if parent is not None and parent.parent_id != 0:
        raise ValidationError("仅支持两级分类：父级必须是一级分类")
    if parent is not None and node is not None:
        if Category.objects.filter(parent_id=node.pk).exists():
            raise ValidationError("该分类下已有子分类，不能改为二级分类")
        if parent.pk == node.pk:
            raise ValidationError("不能将自身设为父级")
        desc = get_descendant_ids(node.pk)
        if parent.pk in desc:
            raise ValidationError("不能将子分类设为父级")


def category_queryset_to_tree(
    qs,
    *,
    include_status: bool = False,
    max_depth: int | None = None,
) -> list[dict[str, Any]]:
    """
    将 Category 查询结果转为嵌套树：parent_id==0 为一级节点，其余按 parent_id 挂在 children。

    - 调用方负责过滤（如公共接口仅 status=enabled）。
    - 返回字段：id、name、sort_order、children；include_status 为 True 时多带 status（管理端）。
    - max_depth 为树的最大深度（一级深度=1）；例如 max_depth=2 表示仅保留一级+二级。
    - 同级按 sort_order、id 排序，保证稳定顺序。
    """
    categories = list(qs.order_by("parent_id", "sort_order", "id"))
    by_parent: dict[int, list[Category]] = {}
    roots: list[Category] = []
    for c in categories:
        if c.parent_id == 0:
            roots.append(c)
        else:
            by_parent.setdefault(c.parent_id, []).append(c)

    def sort_key(x: Category) -> tuple[int, int]:
        return (x.sort_order, x.id)

    def build(node: Category, *, depth: int) -> dict[str, Any]:
        row: dict[str, Any] = {
            "id": node.id,
            "name": node.name,
            "sort_order": node.sort_order,
            "children": [],
        }
        can_have_children = max_depth is None or depth < max_depth
        if can_have_children:
            row["children"] = [
                build(ch, depth=depth + 1) for ch in sorted(by_parent.get(node.id, []), key=sort_key)
            ]
        if include_status:
            row["status"] = node.status
        return row

    return [build(r, depth=1) for r in sorted(roots, key=sort_key)]


def get_ancestor_ids(category_id: int) -> Set[int]:
    """
    返回该分类节点的“祖先集合”，包含自身。
    """
    ids: Set[int] = set()
    cid: int | None = category_id
    while cid:
        row = Category.objects.filter(pk=cid).only("id", "parent_id").first()
        if not row:
            break
        ids.add(row.id)
        if row.parent_id == 0:
            break
        cid = row.parent_id
    return ids


def get_descendant_ids(category_id: int) -> Set[int]:
    """
    返回该分类节点的“后代集合”，包含自身。
    """
    ids: Set[int] = set()
    stack = [category_id]
    while stack:
        cid = stack.pop()
        if cid in ids:
            continue
        ids.add(cid)
        children = Category.objects.filter(parent_id=cid).values_list("id", flat=True)
        stack.extend(list(children))
    return ids


def get_ancestor_or_descendant_ids(category_id: int) -> Set[int]:
    """
    对应你定义的展示口径：
    - 当用户在分类 C 浏览时
    - 若 Listing 的分类 X 与 C 存在祖先-后代关系，则展示

    即：X 属于 (ancestors(C) ∪ descendants(C))，其中集合都包含自身。
    """
    return get_ancestor_ids(category_id) | get_descendant_ids(category_id)
