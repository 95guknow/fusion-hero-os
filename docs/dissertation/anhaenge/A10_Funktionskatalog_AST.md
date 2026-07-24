# A10 — Funktionskatalog (maschinell aus AST)

**Geltung:** Spezifikation (Inventar des Codes, Stand Generator-Lauf).
**Nicht:** Beweis der Korrektheit einzelner Funktionen.
**Designvorlage:** V3.3 — Katalog = Spezifikation; Herleitungen in A01–A09.

**Dateien gesamt:** 200 (fusion_hero_os: 135 · Dashboard: 65) · **Klassen:** 314 · **Top-Level-Funktionen:** 1355

Scan-Wurzeln:
- `fusion_hero_os/`
- `03_Code/Dashboard/`

Regenerieren: `python scripts/generate_anhang_katalog.py`

# Teil I — `fusion_hero_os`

## `fusion_hero_os/bridge/gateway.py`

### class `IPCGateway`
- public: `status`, `dispatch`, `math_status`, `orchestrator_status`
- intern: `__init__`, `_connect`
- def `get_ipc_gateway`

## `fusion_hero_os/bridge/router.py`

- def `_json_safe`
- def `route_dispatch`
- def `_v8_import`
- def `route_list_modules`
- def `handle_ipc_message`

## `fusion_hero_os/config.py`

- def `_env_int`
- def `_env_set`
### class `DispatcherConfig`
- (Datenklasse / ohne Methoden)
- def `_max_workers_or_none`
- def `get_config`
- def `get_port_base`

## `fusion_hero_os/connectors/graph_api.py`

- def `_load_yaml`
- def `_env`
- def `_live_enabled`
### class `GraphConnectorSpec`
- public: `token`, `available`
### class `GraphAPIHub`
- public: `list_connectors`, `status`, `request`, `instagram_publish`, `dispatch`
- intern: `__init__`, `_dry`
- def `build_default_hub`
- def `status_all`

## `fusion_hero_os/core/_mtc_obf.py`

- def `_L`

## `fusion_hero_os/core/api_plane.py`

- def `load_catalog`
- def `_fallback_catalog`
- def `classify_path`
- def `plane_meta`
- def `planes_status`
- def `assert_plane_safe_payload`
- def `main`

## `fusion_hero_os/core/autoload_controller.py`

- def `_now`
- def `_load`
- def `mark_ready`
- def `public_status`
- def `status`
- def `main`

## `fusion_hero_os/core/base_module.py`

### class `EvolutionProposal`
- (Datenklasse / ohne Methoden)
### class `ReviewCriterion`
- (Datenklasse / ohne Methoden)
### class `ReviewResult`
- public: `passed`, `score`, `report`
### class `BaseModule`
- public: `process`, `propose_evolution`, `peer_review`
- intern: `__init__`

## `fusion_hero_os/core/browser_egress.py`

- def `load_config`
- def `_expand`
- def `resolve_profile`
- def `open_url`
- def `open_urls`
- def `status`
- def `main`

## `fusion_hero_os/core/cec.py`

### class `CoEvolutionaryClosure`
- public: `step`
- intern: `__init__`, `_calculate_coherence`

## `fusion_hero_os/core/comaedchen_audio.py`

- def `_now`
- def `_ps`
- def `_process_running`
- def `_ensure_comet`
- def `_ensure_audiorelay`
- def `_svv_path`
- def `_set_default_endpoint`
- def `_phone_online`
- def `_open_comet_surface`
- def `activate`
- def `status`
- def `deactivate_route_note`
- def `main`

## `fusion_hero_os/core/comaedchen_identity.py`

- def `_now`
- def `voice_design_contract`
- def `status`
- def `propagate`
- def `main`

## `fusion_hero_os/core/control_instances.py`

### class `ControlResult`
- public: `to_dict`
### class `ControlReport`
- public: `to_dict`
- def `_load_cfg`
- def `_load_dotenv`
- def `list_instances`
- def `status`
- def `_parse_json_answer`
- def `_invoke_accuracy`
- def `_answer_key`
- def `_consensus`
- def `run_control_panel`
- def `main`

## `fusion_hero_os/core/conversation_archive_inventory.py`

- def `_author_display`
- def `_decode_instance_key`
- def `_safe_public_path`
- def `scan_conversation_archives`
- def `write_dissertation_appendix`
- def `status`
- def `main`

## `fusion_hero_os/core/daemon_self_heal_field_study.py`

### class `ClearwebLens`
- (Datenklasse / ohne Methoden)
### class `HealStep`
- public: `to_dict`
- def `_energy`
- def `_build_qubo`
- def `_hamming`
- def `fixed_point_invert`
- def `qubo_local_search`
- def `run_field_study`
- def `main`

## `fusion_hero_os/core/dashboard/orchestration.py`

### class `DashboardOrchestrator`
- public: `register_agent`, `assign_best_agent`, `get_active_agents`
- intern: `__init__`

## `fusion_hero_os/core/dashboard/workspace.py`

### class `Workspace`
- public: `set`, `get`, `clear`
- intern: `__init__`

## `fusion_hero_os/core/dauer_eupression.py`

- def `_now`
- def `_now_ts`
- def `load_deps`
- def `_builtin_deps`
- def `topo_order`
- def `_probe_node`
- def `pulse`
- def `ensure_continuous`
- def `install`
- def `_load_state`
- def `_save_state`
- def `public_status`
- def `status`
- def `main`

## `fusion_hero_os/core/daycycle_mem.py`

- def `load_config`
- def `_deep_merge`
- def `_cfg`
- def `_p`
- def `mem_path`
- def `state_path`
- def `traffic_path`
- def `protocol_path`
- def `archive_dir`
- def `load_state`
- def `save_state`
- def `_now_local`
- def `_now_utc`
- def `_redact`
- def `_git`
- def `_gh`
- def `private_repo_path`
- def `ensure_dev_branch`
- def `protocol_event`
- def `is_agent_awake`
- def `wake_agent`
- def `check_wake_word`
- def `minute_tick`
- def `hourly_flush`
- def `pr_cycle`
- def `daily_top_merge`
- def `fanout_updates`
- def `log_instance_traffic`
- def `run_due`
- def `status`
- def `main`

## `fusion_hero_os/core/dead_letterbox_pseudo_attack_sim.py`

### class `DeadLetterbox`
- public: `deposit`
### class `PseudoProbe`
- public: `to_dict`
### class `DefenseVerdict`
- public: `to_dict`
### class `MockDefender`
- public: `receive`
- intern: `__init__`, `_forbidden_target`
- def `_synthetic_boxes`
- def `_synthetic_probes`
- def `run_pseudo_attack_sim`
- def `status`
- def `main`

## `fusion_hero_os/core/dependency_atlas.py`

### class `Node`
- (Datenklasse / ohne Methoden)
### class `Edge`
- (Datenklasse / ohne Methoden)
### class `Atlas`
- public: `to_dict`, `epistemik_summary`
- def `_layer_prefixes_from_unified`
- def `assign_layer`
- def `_iter_python_files`
- def `_module_name`
- def `_top_level_imports`
- def `_resolve_absolute`
- def `_resolve_relative`
- def `scan_python`
- def `_parse_cargo_dependencies`
- def `scan_rust`
- def `scan_js`
- def `find_cycles`
- def `build_atlas`
- def `_repo_state_signature`
- def `_layer_prefixes_cached`
- def `build_atlas_cached`
- def `_package_key`
- def `render_mermaid`
- def `render_markdown`
- def `main`

## `fusion_hero_os/core/dispatcher.py`

### class `ModuleNotRegisteredError`
- (Datenklasse / ohne Methoden)
### class `Dispatcher`
- public: `register`, `unregister`, `list_modules`, `dispatch`, `dispatch_many`, `propose_evolution`, `collect_evolution_proposals`, `peer_review`
- intern: `__init__`, `_get`
- def `build_default_dispatcher`
- def `get_default_dispatcher`

## `fusion_hero_os/core/dns_tor_stack.py`

- def `load_config`
- def `_cfg`
- def `_tor_data`
- def `find_tor_exe`
- def `start_tor_if_possible`
- def `_port_open`
- def `_parse_qname`
- def `_encode_name`
- def `_build_query`
- def `_forward_udp`
- def `resolve_once`
- def `_handle_query`
- def `serve`
- def `status`
- def `configure_tailscale_dns`
- def `main`

## `fusion_hero_os/core/doppelrekursionsrollation.py`

### class `PCG64`
- public: `next_u64`, `fill`
- intern: `__init__`, `_step`
- def `_rotl_bytes`
- def `_sha256`
- def `_sha512`
- def `polymesh_day_seed`
- def `polymesh_hash_number_1`
- def `doppelrekursionsrollation`
- def `gpg_hash_payload`
- def `gpg_hash_with_prng`
- def `run_day_rollation`
- def `main`

## `fusion_hero_os/core/dual_timeline_training.py`

### class `FileEvent`
- public: `to_dict`
### class `TrainSample`
- public: `to_dict`
- def `load_config`
- def `_cfg`
- def `output_dir`
- def `_sha16`
- def `_layer_for`
- def `_geltung_hits`
- def `virtual_timelines_enabled`
- def `heroic_score_for_text`
- def `_tau`
- def `iter_candidate_files`
- def `scan_files`
- def `_chunk_text`
- def `_samples_from_file`
- def `build_samples`
- def `consistency_report`
- def `run_auto_train`
- def `status`
- def `main`

## `fusion_hero_os/core/erkenntnis_archiv.py`

- def `_state_dir`
- def `_now`
- def `_read_json`
- def `_write_json`
- def `_append_jsonl`
- def `_read_jsonl`
- def `_summarize_hour`
### class `ErkenntnisArchiv`
- public: `record`, `status`, `force_rollover`
- intern: `__init__`, `_hourly_path`, `_rollover_state_path`, `_daily_path`, `_weekly_path`, `_monthly_path`, `_yearly_path`, `_keys`, `_last_keys`, `_save_keys`, `_maybe_rollover`, `_roll_hour_into_day`, `_roll_day_into_week`, `_roll_week_into_month`, `_roll_month_into_year`
- def `record`
- def `status`

## `fusion_hero_os/core/eudaemon_agent.py`

### class `CorridorStep`
- public: `to_dict`
- def `_now`
- def `_plane_hint`
- def `_classify_body`
- def `walk_corridor`
- def `meister_integrity`
- def `eudaimonia_corridor_check`
- def `act_other_side`
- def `run_eudaemon`
- def `main`

## `fusion_hero_os/core/god_layer_seal.py`

- def `_now`
- def `_norm_token`
- def `_token_hash`
- def `_default_unlock_hash`
- def `_load`
- def `_save`
- def `is_sealed`
- def `can_read`
- def `can_write`
- def `require_write`
- def `seal_god_layer`
- def `_bind_private_person_vault`
- def `try_unlock`
- def `public_status`
- def `status`
- def `main`

## `fusion_hero_os/core/google_one_sicherung.py`

- def `_open_browser_url`
- def `load_config`
- def `_expand`
- def `_local_root`
- def `_is_excluded`
- def `_match_include`
- def `_sha16_file`
- def `activate`
- def `run_snapshot`
- def `_find_drivefs_exe`
- def `_drivefs_running`
- def `_find_my_drive_paths`
- def `setup_desktop`
- def `setup_phone`
- def `status`
- def `main`

## `fusion_hero_os/core/grok_interconnect.py`

### class `GrokNode`
- (Datenklasse / ohne Methoden)
### class `GrokEdge`
- (Datenklasse / ohne Methoden)
### class `InterconnectGraph`
- public: `to_dict`
- def `probe_http`
- def `_tcp_open`
- def `_read_json`
- def `capture`
- def `evolve`
- def `get_graph`
- def `_persist`

## `fusion_hero_os/core/grok_route_table.py`

### class `RouteTarget`
- public: `to_dict`
- def `resolve`
- def `route_message`
- def `all_routes`

## `fusion_hero_os/core/headset_layers.py`

- def `_now`
- def `_default_state`
- def `load_state`
- def `save_state`
- def `_phone_link_snapshot`
- def `set_mesh_only`
- def `is_mesh_only`
- def `banner`
- def `status`
- def `_probe_default_device`
- def `enable`
- def `disable`
- def `_norm`
- def `set_active`
- def `apply_active_route`
- def `_svv_set_default`
- def `activate_stack`
- def `main`

## `fusion_hero_os/core/hero_autoupdate.py`

- def `_utc_now`
- def `_repo_root`
- def `_load_yaml_config`
- def `_env_float`
- def `_env_bool`
### class `HeroAutoupdateConfig`
- public: `load`
### class `HeroAutoupdateState`
- public: `to_dict`, `from_dict`
### class `HeroAutoupdateService`
- public: `state_file`, `notify_android`, `touch`, `idle_sec`, `status`, `tick`, `notify_startup`
- intern: `__init__`, `_load_state`, `_save_state`, `_push_event`, `_read_version`, `_git_head`, `_git_behind_origin`, `_health`
- def `get_hero_autoupdate`
- def `reset_hero_autoupdate_for_tests`

## `fusion_hero_os/core/heroic_core.py`

### class `HeroicCore`
- public: `register_module`, `get_llm`, `get_sisyphos_state`, `enforce_fail_closed`, `trigger_psycholysis_if_needed`, `status`
- intern: `__init__`, `_dummy_context`
- def `get_heroic_core`

## `fusion_hero_os/core/heroic_core_orchestrator.py`

### class `MasterSeed`
- public: `state_hash`, `verify_integrity`, `public_display`
### class `PMSEvidenceSpine`
- public: `available`, `execute_operator_chain`, `validate_chain`
- intern: `__init__`, `_run`
### class `QuadCoreBridge`
- public: `invoke_phoenix_mode`, `process_query`, `ask_llm`, `run_ascension_generation`
- intern: `__init__`, `_flush_volatile_memory`
- def `bootstrap_v8_system`

## `fusion_hero_os/core/heroic_math_engine.py`

### class `HeroicMatrixEngine`
- public: `compute_commutator`, `check_reciprocity_condition`, `check_transpose_reciprocity`
- intern: `__init__`
### class `OrthogonalProjector`
- public: `project`, `is_idempotent`, `is_symmetric`, `spectrum_in_01`, `is_nonexpansive_for`
- intern: `__init__`
### class `StableCoreLattice`
- public: `is_less_or_equal`, `get_join`
- intern: `__init__`, `_apply_transitive_closure`
### class `RepairedStructureIP`
- public: `compute_stability`, `check_compatibility`, `check_monotone_domain`, `fusion_operator`
- intern: `__init__`
### class `BanachContractionSeed`
- public: `apply`, `fixpoint`, `iterate`, `verify_contraction_bound`
- intern: `__init__`
- def `run_sandbox_verification`

## `fusion_hero_os/core/horkrux_bottom_up.py`

- def `load_config`
- def `_expand`
- def `_git`
- def `_is_git`
- def `_sync_git`
- def `_check_state_dir`
- def `_check_skill`
- def `_check_remote`
- def `_scan_worktree_root`
- def `_preserve_horcrux`
- def `run_bottom_up`
- def `status`
- def `main`

## `fusion_hero_os/core/inference_scheduler_qubo.py`

### class `ScheduleProblem`
- public: `n`, `total_cost`
- intern: `__post_init__`
- def `build_qubo`
- def `greedy_schedule`
- def `solve_schedule`
- def `random_problem`

## `fusion_hero_os/core/inside_out_inventory.py`

### class `Item`
- public: `to_dict`
- def `_expand`
- def `_class_hint`
- def `_iter_files`
- def `_match_repo_globs`
- def `_record`
- def `run_inventory`
- def `status`
- def `main`

## `fusion_hero_os/core/layer_distance_crosscheck.py`

- def `build_adjacency`
- def `distance_n_neighbors`
### class `BlindSpotCandidate`
- public: `to_dict`
- def `find_blind_spot_candidates`
- def `crosscheck_all`
- def `build_adjacency_from_fusion_unified`
- def `crosscheck_real_layers`

## `fusion_hero_os/core/layer_registry.py`

- def `_load_yaml`
- def `_load_json`
### class `LayerStatus`
- public: `to_dict`
- def `_paths_from_config`
- def `_check_mesh_layer`
- def `_check_intelligence_layer`
- def `_check_vr_layer`
- def `_check_kernel_layer`
- def `_check_ascension_layer`
- def `_check_knowledge_layer`
- def `erkenntnisse_summary`
- def `get_layer_status`
- def `_build_status`
- def `get_all_layer_status`

## `fusion_hero_os/core/masterseed_public.py`

- def `_b32_crockford`
- def `_check4`
### class `PublicMasterSeedView`
- public: `to_dict`
- intern: `__str__`
- def `_platform_version_default`
- def `public_fingerprint`
- def `display_id_from_fingerprint`
- def `parse_display_id`
- def `public_view`
- def `assert_unique_display`

## `fusion_hero_os/core/masterseed_sync.py`

### class `SyncState`
- public: `state_hash`
- def `mutual_sync`
- def `sync_evolutions`
- def `identity_preservation_score`

## `fusion_hero_os/core/masterseed_vault.py`

### class `ShardMeta`
- public: `to_dict`
- def `vault_root`
- def `_load_split_config`
- def `list_module_split`
- def `_qubo_perm_from_seed`
- def `qubo_permute`
- def `qubo_unpermute`
- def `_gpg_available`
- def `_gpg_encrypt`
- def `_gpg_decrypt`
- def `seal_function_shard`
- def `open_function_shard`
- def `seal_all_modules`
- def `export_public_display`
- def `status`
- def `main`

## `fusion_hero_os/core/meister_hasch_optimize.py`

### class `OptimizeConfig`
- public: `to_dict`
### class `ProbeResult`
- public: `to_dict`
### class `LensReport`
- public: `passed`, `score`, `to_dict`
### class `OptimizeReport`
- public: `overall_passed`, `to_dict`
- def `_platform_version`
- def `_sha256_file`
- def `_now_iso`
- def `_fable5_probes`
- def `_mythos5_probes`
- def `_hypertarnkappe_probes`
- def `_hyperpanzerknacker_probes`
- def `_optimizations_from_lenses`
- def `run_optimize`
- def `status`

## `fusion_hero_os/core/models.py`

### class `Task`
- (Datenklasse / ohne Methoden)
### class `TaskResult`
- (Datenklasse / ohne Methoden)

## `fusion_hero_os/core/mugen_tsuky_chan.py`

- def `_obf`
- def `status`
- def `day_hash_1`
- def `roll`
- def `mint_once`
- def `propagate`

## `fusion_hero_os/core/multimodal_protocol.py`

### class `InventoryEntry`
- (Datenklasse / ohne Methoden)
- def `_sha256`
- def `_extract_text`
- def `_extract_pdf`
- def `_extract_image`
- def `_mutagen_info`
- def `_extract_audio`
- def `_extract_video`
- def `classify`
- def `_iter_archive_files`
- def `build_inventory`
- def `_archive_signature`
- def `build_inventory_cached`
- def `_load_frameworks`
- def `provider_access_status`
- def `routing_matrix`
- def `summary`
- def `to_dict`
- def `main`

## `fusion_hero_os/core/operator_identity.py`

- def `_now`
- def `load_identity`
- def `save_identity_template`
- def `operator_role`
- def `operator_id`
- def `author_for_publication`
- def `public_operator_view`
- def `is_person_bound`
- def `extract_status`
- def `main`

## `fusion_hero_os/core/ops_deploy.py`

- def `status`
- def `deploy`
- def `main`

## `fusion_hero_os/core/ops_merge.py`

- def `status`
- def `merge_both`
- def `main`

## `fusion_hero_os/core/ops_push.py`

- def `status`
- def `push_public`
- def `main`

## `fusion_hero_os/core/ops_vocabulary.py`

- def `load_ops`
- def `meaning_of`
- def `status`
- def `main`

## `fusion_hero_os/core/persona_signature.py`

- def `_display_name`
- def `signature_block`
- def `expand_signature_triggers`
- def `signature_status`
- def `main`

## `fusion_hero_os/core/poly_fa_write_gate.py`

- def `_now`
- def `_now_ts`
- def `hostname`
- def `_norm_token`
- def `_token_hash`
- def `default_policy`
- def `load_policy`
- def `save_policy`
- def `install_handover_policy`
- def `_save_json`
- def `_load_json`
- def `is_authorized_desktop`
- def `_phrase_ok`
- def `_poly_plane_ok`
- def `request_write`
- def `approve_request_with_poly_fa`
- def `_active_grants`
- def `can_write_now`
- def `revoke_grant`
- def `public_status`
- def `status`
- def `main`

## `fusion_hero_os/core/poly_mesh_cost_function.py`

### class `BurnBreakdown`
- public: `total_eur_h`, `total_eur_month`, `to_dict`
- def `compute_burn`
- def `compute_feu`
- def `resolve_margin`
- def `tier_price`
- def `placement_cost`
- def `evaluate_full`
- def `cost_function_status`
- def `main`

## `fusion_hero_os/core/poly_mesh_once_url.py`

- def `_state_dir`
- def `_secret_path`
- def `_ledger_path`
- def `get_or_create_secret`
- def `_b64url`
- def `_b64url_decode`
- def `encrypt_mesh_ip`
- def `decrypt_mesh_ip`
- def `heroic_dns_label`
- def `pick_heroic_name`
- def `_load_ledger`
- def `_save_ledger`
### class `OnceUrl`
- public: `once_url`, `mesh_once_url`, `to_dict`
- def `mint_once_url`
- def `redeem_once`
- def `mint_from_tailscale`

## `fusion_hero_os/core/poly_mesh_orchestrator.py`

- def `_now`
- def `_load_router`
- def `_mesh_inventory`
- def `_algo_class`
- def `_dispatch_action`
- def `coherence_score`
- def `plan_only`
- def `_build_waves`
- def `_execute_hooks`
- def `orchestrate`
- def `status`
- def `main`

## `fusion_hero_os/core/poly_mesh_os_port.py`

- def `_now`
- def `load_manifest`
- def `_ts_json`
- def `inventory_mesh`
- def `_tier_for_host`
- def `build_port_registry`
- def `try_mesh_serve_dashboard`
- def `port_status`
- def `port_os`
- def `main`

## `fusion_hero_os/core/poly_mesh_router.py`

- def `load_catalog`
- def `_find_kubectl`
- def `probe_gke`
- def `_online_tiers_from_tailscale`
- def `_pick_tier`
- def `route`
- def `route_all`
- def `assert_not_local_dual_start`
- def `status`
- def `main`

## `fusion_hero_os/core/power_mesh_fusion_evolution.py`

### class `StratumState`
- public: `to_dict`
### class `Genome`
- public: `to_dict`
### class `GenerationRecord`
- public: `to_dict`
### class `EvolutionReport`
- public: `to_dict`
- def `load_config`
- def `_output_dir`
- def `_file_bytes`
- def `scan_strata`
- def `_stratum_map`
- def `_normalize`
- def `_default_genome`
- def `_component_scores`
- def `fitness`
- def `_mutate`
- def `_crossover`
- def `run_evolution`
- def `status`
- def `main`

## `fusion_hero_os/core/pseudo_horcrux.py`

- def `_canonical`
- def `_checksum`
### class `HorcruxShard`
- (Datenklasse / ohne Methoden)
- def `_encode_json`
- def `_decode_json`
- def `_encode_csv`
- def `_decode_csv`
- def `_encode_b64`
- def `_decode_b64`
### class `PseudoHorcruxStore`
- public: `preserve`, `restore`, `integrity_report`
- intern: `__init__`, `_shard_path`, `_iter_shard_paths`, `_read_shard`, `_best_shard_unlocked`
### class `AutosaveStats`
- (Datenklasse / ohne Methoden)
### class `AutosaveDaemon`
- public: `start`, `stop`, `mark_dirty`, `snapshot_stats`
- intern: `__init__`, `__enter__`, `__exit__`, `_loop`, `_save_once`

## `fusion_hero_os/core/pseudo_inhouse_ai.py`

### class `PseudoInhouseResult`
- public: `to_dict`, `openai_chat_completion`
- def `_load_yaml_catalog`
- def `catalog`
- def `_framework_status`
- def `_ollama_live`
- def `status`
- def `list_models`
- def `_internal_complete`
- def `complete`
- def `main`

## `fusion_hero_os/core/pseudo_inhouse_creative.py`

### class `CreativeResult`
- public: `to_dict`
- def `output_dir`
- def `_load_yaml`
- def `catalog`
- def `_pil`
- def `_font`
- def `_parse_size`
- def `_slug`
- def `_stamp`
- def `_palette`
- def `create_image`
- def `create_graphics`
- def `_xml_escape`
- def `create_pdf`
- def `create_video`
- def `create`
- def `status`
- def `list_artifacts`
- def `openai_image_response`
- def `main`

## `fusion_hero_os/core/psycholysis_trigger.py`

### class `PsycholysisTrigger`
- public: `should_trigger`, `trigger`, `log_somatic_practice`, `complete_session`
- intern: `__init__`

## `fusion_hero_os/core/pure_core_coevolution.py`

- def `_now`
- def `_read_yaml`
### class `StrengthEntry`
- public: `to_dict`
### class `TransferEvent`
- public: `to_dict`
### class `CoevolutionReport`
- public: `to_dict`
- def `_default_catalog`
- def `load_catalog`
- def `_scan_evidence`
- def `_entries`
- def `core_strength_ids`
- def `foreign_strength_ids`
- def `crosspoll_sources`
- def `assert_core_not_replaced`
- def `radiate_core_to_foreign`
- def `ingest_foreign_gated`
- def `coevolve_step`
- def `mutual_cycle`
- def `export_report`
- def `status`
### class `PureCoreMembrane`
- public: `step`, `cycle`, `status`
- intern: `__init__`

## `fusion_hero_os/core/push_layer_guard.py`

### class `PushDecision`
- public: `to_dict`
- def `load_config`
- def `_git`
- def `_match_any`
- def `_layers_for_paths`
- def `_load_dotenv_files`
- def `_secret_intent`
- def `_intent_present`
- def `_is_auto_save`
- def `_remote_ok`
- def `_platform_ok`
- def `_collect_push_files`
- def `evaluate_push`
- def `status`
- def `install_hint`
- def `main`

## `fusion_hero_os/core/quantum_cognition.py`

- def `_as_state`
- def `_check_projector`
- def `projector_from_vectors`
### class `BeliefState`
- public: `prob`, `collapse`, `prob_sequence`
- intern: `__init__`
- def `order_effect`
- def `qq_equality_residual`
- def `interference_term`
### class `TwoLevelOscillator`
- public: `unitary`, `unitary_via_spectral`, `transition_probability`, `evolve`
- intern: `__init__`

## `fusion_hero_os/core/quantum_dictionaries.py`

- def `canonical_key`
### class `_Entry`
- (Datenklasse / ohne Methoden)
### class `QuantumDictionary`
- public: `get_or_compute`, `invalidate`, `stats`
- intern: `__init__`
- def `get_quantum_dictionary`
- def `registry_stats`

## `fusion_hero_os/core/race_guard.py`

- def `_as_path`
### class `FileLock`
- public: `acquire`, `release`
- intern: `__init__`, `__enter__`, `__exit__`
- def `file_lock`
- def `atomic_write_text`
- def `atomic_write_json`
- def `locked_atomic_write_json`
- def `_read_json`
- def `compare_and_swap_json`
### class `RaceConditionGuard`
- public: `write_json`, `write_text`, `cas`
- def `race_stress_test`

## `fusion_hero_os/core/rhe.py`

### class `EmbodimentState`
- (Datenklasse / ohne Methoden)
### class `RustHybridEmbodiment`
- public: `update_from_body`, `update_from_theory`, `get_state`
- intern: `__init__`, `_recalculate_coherence`

## `fusion_hero_os/core/schwerkraftserver.py`

- def `_state_dir`
- def `_sha256`
- def `control_a_lossless`
- def `control_b_lossless`
- def `dual_multi_model_control`
- def `_git_log_rows`
- def `ingest_commit_history`
- def `execute`
- def `main`

## `fusion_hero_os/core/tailscale_quantize_selfmod.py`

- def `load_config`
- def `_cfg`
- def `state_dir`
- def `_ts_exe`
- def `tailscale_snapshot`
### class `AssistNode`
- public: `to_dict`
### class `QuantizeParams`
- public: `to_dict`
- def `_clamp`
- def `_mesh_scale`
- def `ensure_assist_nodes`
- def `self_modulate`
- def `_make_qubo`
- def `_quantize_matrix`
- def `_anneal_once`
- def `run_quantize`
- def `run_full_cycle`
- def `status`
- def `main`

## `fusion_hero_os/core/universal_llm_router.py`

### class `SisyphosCycle`
- public: `step`, `get_state`
### class `FailClosed`
- public: `enforce`
### class `UnifiedHeroicLLMCore`
- public: `get_best_assignment`, `ask`, `aask`, `initiate_recovery`, `status`
- intern: `__init__`, `_build_heroic_context`, `_classify`, `_score`
- def `get_unified_llm_core`

## `fusion_hero_os/core/x402_hackability_audit.py`

- def `load_config`
### class `GateResult`
- public: `to_dict`
### class `MathCheck`
- public: `to_dict`
### class `AuditReport`
- public: `to_dict`
- def `heroic_math_checks`
- def `_default_gate_answers`
- def `audit`
- def `risk_score`
- def `_persist_report`
- def `emit_warning`
- def `status`
- def `main`

## `fusion_hero_os/core/x402_sandbox_audit.py`

### class `SandboxConfig`
- public: `to_dict`
### class `PaymentAuth`
- (Datenklasse / ohne Methoden)
### class `EvidenceCase`
- public: `to_dict`
### class `MockX402Server`
- public: `challenge`, `grant`
- intern: `__init__`, `_bind_ok`
### class `MockClient`
- public: `pay_and_request`
- intern: `__init__`
- def `_case_replay`
- def `_case_finality`
- def `_case_binding`
- def `_case_unverified`
- def `_case_cache_header`
- def `_case_allowlist`
- def `simulate_successful_attack`
- def `run_sandbox_audit`
- def `status`
- def `main`

## `fusion_hero_os/core/zitterpolymesh.py`

### class `LaneKind`
- (Datenklasse / ohne Methoden)
### class `LaneProfile`
- public: `as_dict`
- def `_pvht_factor`
- def `detect_lanes`
### class `ZitterJitter`
- public: `delay`
### class `ZitterTask`
- (Datenklasse / ohne Methoden)
### class `MeshValidationError`
- (Datenklasse / ohne Methoden)
### class `ZitterPolyMesh`
- public: `add_task`, `validate`, `run`
- intern: `__init__`
- def `_op_cpu_sum_squares`
- def `_op_mem_shard_roundtrip`
- def `_op_gpu_matmul`
- def `_solve_qubo_stdlib`
- def `_op_qpu_min_qubo`
- def `builtin_ops`
- def `load_pipeline`
- def `mesh_from_pipeline`
- def `_cli`

## `fusion_hero_os/engine/mainframe.py`

- def `_get_pool`
- def `_load_rust_backend`
- def `get_rust_backend`
### class `QUBOProblem`
- intern: `__init__`
### class `SolverResult`
- intern: `__init__`
### class `QUBOSolverConfig`
- intern: `__init__`
- def `_simulated_annealing_kernel`
- def `simulated_annealing`
- def `local_search`
- def `make_Q`
- def `_sa_kernel_trace`
- def `_anneal_one`
- def `parallel_anneal`
- def `warmup_kernels`
### class `SolverBackend`
- public: `solve`
### class `ClassicalBackend`
- public: `solve`
- intern: `__init__`
### class `SelfModifyCoreModule`
- public: `register_audit_hook`
- intern: `__init__`
### class `GenerationalEvolutionProtocolCoreModule`
- public: `run_generation`, `evolve`
- intern: `__init__`, `_clip`, `_random_genome`, `_mutate`, `_target`, `_fitness`, `_init_population`
### class `CriticalMetaAnalysisCoreModule`
- public: `analyze`
### class `ExecutableAuditAgent`
- intern: `__init__`
### class `QUBOIntegrationCoreModule`
- public: `get_ascension_state`, `run_ascension_generation`, `execute_secure_run`, `execute_parallel_run`
- intern: `__init__`, `_interlock_core_hooks`

## `fusion_hero_os/engine/mining_qubo.py`

### class `ExcavatorConnector`
- public: `info`, `speeds`, `workers`
- intern: `_call`
- def `estimate_profit_matrix`
- def `build_profit_switching_qubo`
- def `decode_assignment`
- def `assignment_profit`
- def `optimize_switching`
- def `_mock_rig`
- def `_demo`

## `fusion_hero_os/engine/rust_backend.py`

- def `parallel_anneal_rust`

## `fusion_hero_os/integrations/phone_link/reader.py`

### class `RealWorldContactBlocked`
- (Datenklasse / ohne Methoden)
- def `deny_realworld_contact_action`
### class `PhoneLinkSnapshot`
- public: `to_dict`
- def `_package_root`
- def `_discover_database`
- def `_filetime_to_iso`
- def `_mask_address`
- def `_is_host_running`
### class `PhoneLinkReader`
- public: `database_path`, `recent_conversations`, `recent_messages`, `counts`, `snapshot`
- intern: `__init__`, `_query`
- def `phone_link_status`

## `fusion_hero_os/mcp/fhero_mcp_server.py`

- def `_tool_layer0_verify`
- def `_tool_schedule_qubo`
- def `_result`
- def `_error`
- def `handle_message`
- def `main`

## `fusion_hero_os/meta/api.py`

- def `get_service`
- def `grant_consent`
- def `ingest`
- def `activate`
- def `associate`
- def `optimize`
- def `audit_trail`
- def `create_app`

## `fusion_hero_os/meta/cli.py`

- def `run_demo`
- def `main`

## `fusion_hero_os/meta/consent.py`

- def `_utcnow`
### class `Purpose`
- (Datenklasse / ohne Methoden)
### class `ConsentError`
- (Datenklasse / ohne Methoden)
### class `ConsentGrant`
- public: `is_active`, `expires_at`, `to_public_dict`
### class `AuditEvent`
- public: `to_dict`
- def `_hash_event`
### class `AuditLog`
- public: `append`, `verify`, `events`, `events_for`
- intern: `__init__`, `__len__`
### class `ConsentStore`
- public: `grant`, `revoke`, `find_active`, `authorize`
- intern: `__init__`

## `fusion_hero_os/meta/coupling.py`

- def `jacobian_fd`
- def `spectral_radius`
- def `operator_norm`
### class `ContractionResult`
- public: `to_dict`
- def `is_contraction`
### class `FixedPointResult`
- public: `to_dict`
- def `iterate_to_fixed_point`

## `fusion_hero_os/meta/fixtures/__init__.py`

- def `load_neutral_fixture`

## `fusion_hero_os/meta/graph.py`

### class `GraphError`
- (Datenklasse / ohne Methoden)
- def `_utcnow_iso`
- def `_canonical_number`
### class `Provenance`
- public: `to_dict`, `now`
### class `GraphSchema`
- public: `to_dict`
### class `Node`
- public: `to_dict`
### class `Edge`
- public: `to_dict`
### class `PropertyGraph`
- public: `add_node`, `add_edge`, `nodes`, `edges`, `snapshot`
- intern: `__init__`
### class `GraphSnapshot`
- public: `schema`, `nodes`, `edges`, `content_hash`, `snapshot_id`, `build`, `to_canonical_json_static`, `to_canonical_json`, `to_dict`, `node_matrix`, `adjacency`
- intern: `__init__`, `_validate`, `_canonical_payload`, `_hash`

## `fusion_hero_os/meta/hebbian.py`

### class `HebbianError`
- (Datenklasse / ohne Methoden)
- def `_key`
### class `HebbianConfig`
- intern: `__post_init__`
### class `HebbianAssociationMemory`
- public: `update`, `update_many`, `decay_all`, `weight`, `delete`, `delete_slot`, `items`, `to_matrix`
- intern: `__init__`, `_clip`, `__len__`

## `fusion_hero_os/meta/pipeline.py`

### class `MetaNeuralService`
- public: `grant_consent`, `revoke_consent`, `sweep_expired`, `ingest`, `snapshot_for`, `activate`, `associate`, `analyze_convergence`, `optimize`, `audit_trail`
- intern: `__init__`, `_require`, `_purge_subject_state`, `_purge_if_expired`

## `fusion_hero_os/meta/qubo_bridge.py`

### class `QUBOBridgeError`
- (Datenklasse / ohne Methoden)
### class `QUBOProblem`
- public: `size`
### class `QUBOResult`
- public: `to_dict`
- def `build_qubo`
- def `energy`
- def `_anneal_numpy`
- def `_brute_force`
- def `solve_qubo`
- def `_try_qb_qubo`

## `fusion_hero_os/meta/schemas.py`

### class `ConsentGrantRequest`
- (Datenklasse / ohne Methoden)
### class `ConsentGrantResponse`
- (Datenklasse / ohne Methoden)
### class `NodeFixture`
- (Datenklasse / ohne Methoden)
### class `EdgeFixture`
- (Datenklasse / ohne Methoden)
### class `IngestRequest`
- (Datenklasse / ohne Methoden)
### class `SnapshotResponse`
- (Datenklasse / ohne Methoden)
### class `ActivateRequest`
- (Datenklasse / ohne Methoden)
### class `ActivationReportResponse`
- (Datenklasse / ohne Methoden)
### class `AssociateRequest`
- (Datenklasse / ohne Methoden)
### class `ConvergenceResponse`
- (Datenklasse / ohne Methoden)
### class `OptimizeRequest`
- (Datenklasse / ohne Methoden)
### class `OptimizeResponse`
- (Datenklasse / ohne Methoden)
### class `AuditEventResponse`
- (Datenklasse / ohne Methoden)
### class `AuditTrailResponse`
- (Datenklasse / ohne Methoden)

## `fusion_hero_os/meta/vault.py`

### class `VaultError`
- (Datenklasse / ohne Methoden)
### class `VaultUnavailableError`
- (Datenklasse / ohne Methoden)
### class `VaultAuthorizationError`
- (Datenklasse / ohne Methoden)
### class `SubjectRef`
- public: `derive`
### class `VaultResolver`
- public: `is_configured`, `resolve`
### class `NullVaultResolver`
- public: `is_configured`, `resolve`
- intern: `__init__`
### class `InMemoryVaultResolver`
- public: `put`, `is_configured`, `resolve`
- intern: `__init__`
- def `default_resolver`

## `fusion_hero_os/meta/working_memory.py`

### class `WorkingMemoryError`
- (Datenklasse / ohne Methoden)
### class `ActivationReport`
- public: `to_dict`
### class `WorkingMemorySpace`
- public: `slots`, `step_index`, `activate`, `step`, `activation`, `vector`, `norm`, `report`, `reset`
- intern: `__init__`, `_clip`

## `fusion_hero_os/methodology/connectors.py`

### class `BaseConnector`
- public: `available`, `status`
- intern: `__init__`, `_dry_run`, `_delegate`, `__repr__`
### class `GitHubConnector`
- public: `commit`, `tag`, `create_repo`
### class `DriveConnector`
- public: `upload`, `download`, `list_files`
### class `VercelConnector`
- public: `deploy`, `list_deployments`
### class `GmailConnector`
- public: `send`, `parse_replies`
### class `XAPIConnector`
- public: `search`, `trends`, `post`
- intern: `__init__`
### class `InstagramConnector`
- public: `publish`, `me`
### class `MetaGraphConnector`
- public: `me`, `request`
### class `ConnectorRegistry`
- public: `default`, `register`, `get`, `inject`, `available`, `plan`
- def `_demo`

## `fusion_hero_os/methodology/core_modules.py`

### class `PeerReviewCoreModule`
- public: `review`, `report`
### class `_Stage`
- (Datenklasse / ohne Methoden)
### class `ErkenntnisprozessCoreModule`
- public: `current_stage`, `advance`, `is_complete`, `report`
- intern: `__init__`
### class `FormalClassification`
- (Datenklasse / ohne Methoden)
### class `FormalMathematicsCoreModule`
- public: `classify`, `report`
### class `V3_3StructureCoreModule`
- public: `skeleton`, `render_markdown`
### class `ArchivePlan`
- (Datenklasse / ohne Methoden)
### class `AutomaticArchivingCoreModule`
- public: `build_plan`
### class `Milestone`
- (Datenklasse / ohne Methoden)
### class `RoadmapCoreModule`
- public: `add`, `complete`, `next_steps`, `next_step`, `report`
- intern: `__init__`, `_deps_erfuellt`
- def `_selbsttest`

## `fusion_hero_os/methodology/knowledge.py`

### class `Module`
- (Datenklasse / ohne Methoden)
### class `Decision`
- (Datenklasse / ohne Methoden)
### class `Repo`
- (Datenklasse / ohne Methoden)
### class `FileVersion`
- (Datenklasse / ohne Methoden)
- def `get_decision`
- def `list_modules`
- def `_md_modules`
- def `as_markdown`

## `fusion_hero_os/modules/automatic_archiving.py`

### class `AutomaticArchivingCoreModule`
- public: `process`
- intern: `__init__`

## `fusion_hero_os/modules/builder_profile/__init__.py`

- def `_find_foundation_roots`
- def `status`
### class `BuilderProfileModule`
- public: `process`, `propose_evolution`

## `fusion_hero_os/modules/code_review.py`

### class `PeerReviewCoreModule`
- public: `process`, `peer_review`
- intern: `_evaluate`

## `fusion_hero_os/modules/conversation_context.py`

### class `ConversationTurn`
- (Datenklasse / ohne Methoden)
### class `ConversationContextCoreModule`
- public: `process`
- intern: `__init__`

## `fusion_hero_os/modules/formal_mathematics.py`

### class `FormalMathematicsCoreModule`
- public: `process`
- intern: `__init__`

## `fusion_hero_os/modules/generational_evolution.py`

### class `GenerationalEvolutionProtocolCoreModule`
- public: `process`, `status`
- intern: `__init__`, `_ensure_impl`

## `fusion_hero_os/modules/hero_autoupdate.py`

### class `HeroAutoupdateCoreModule`
- public: `process`

## `fusion_hero_os/modules/heroic_llm_ea/evolution.py`

### class `EvolutionConfig`
- (Datenklasse / ohne Methoden)
### class `EvolutionarySelector`
- public: `run_generation`
- intern: `__init__`

## `fusion_hero_os/modules/heroic_llm_ea/fitness.py`

- def `fitness_function`
- def `score_with_peer_review`

## `fusion_hero_os/modules/heroic_llm_ea/memory.py`

### class `ProposalRecord`
- public: `proposal_id`
### class `MutationMemory`
- public: `remember`, `elites`, `best`, `mutate_from_elite`, `snapshot`
- intern: `__init__`

## `fusion_hero_os/modules/heroic_llm_ea/orchestrator.py`

### class `HeroicLLMEAOrchestrator`
- public: `with_campfire_templates`, `process`, `peer_review`
- intern: `__init__`, `_score_proposal`, `_propose_once`, `_evolve_many`, `_provider_status`

## `fusion_hero_os/modules/heroic_llm_ea/providers.py`

### class `LLMProvider`
- public: `propose`
### class `StubLLMProvider`
- public: `propose`
### class `CallableLLMProvider`
- public: `propose`
- intern: `__init__`
### class `CampfireTemplateProvider`
- public: `propose`
- intern: `__init__`, `_load`

## `fusion_hero_os/modules/image_orchestrator/job_queue.py`

### class `JobStatus`
- (Datenklasse / ohne Methoden)
### class `ImageJob`
- public: `to_dict`
### class `ImageJobQueue`
- public: `create`, `update`, `get`, `list_recent`
- intern: `__init__`, `_trim`

## `fusion_hero_os/modules/image_orchestrator/orchestrator.py`

### class `HeroicImageOrchestrator`
- public: `set_provider`, `process`, `peer_review`
- intern: `__init__`, `_load_config`, `_build_pipeline`

## `fusion_hero_os/modules/image_orchestrator/pipeline.py`

### class `ImagePipeline`
- public: `run`
- intern: `__init__`

## `fusion_hero_os/modules/image_orchestrator/prompt_builder.py`

- def `build_prompt`
- def `validate_identity`

## `fusion_hero_os/modules/image_orchestrator/providers.py`

### class `ImageProvider`
- public: `render`
### class `DryRunImageProvider`
- public: `render`
### class `CallableImageProvider`
- public: `render`
- intern: `__init__`

## `fusion_hero_os/modules/image_orchestrator/rate_limiter.py`

### class `RateLimitConfig`
- (Datenklasse / ohne Methoden)
### class `TokenBucketRateLimiter`
- public: `allow`, `status`
- intern: `__init__`, `_prune`
### class `DualRateLimiter`
- public: `allow`, `status`
- intern: `__init__`

## `fusion_hero_os/modules/live_process_tracking.py`

### class `TrackedProcess`
- (Datenklasse / ohne Methoden)
### class `LiveProcessTrackingCoreModule`
- public: `process`, `snapshot`
- intern: `__init__`

## `fusion_hero_os/modules/mainframe_laden/__init__.py`

- def `status`
- def `load_all`
### class `MainframeLadenModule`
- public: `process`, `propose_evolution`

## `fusion_hero_os/modules/mer.py`

### class `MERModule`
- public: `process`, `optimize`
- def `_clamp01`

## `fusion_hero_os/modules/phone_link.py`

### class `PhoneLinkCoreModule`
- public: `process`
- intern: `__init__`

## `fusion_hero_os/modules/qubo_integration.py`

### class `QUBOIntegrationCoreModule`
- public: `process`
- intern: `__init__`

## `fusion_hero_os/modules/self_modify.py`

### class `SelfModifyCoreModule`
- public: `process`, `propose_evolution`, `history`
- intern: `__init__`, `_record_proposal`

## `fusion_hero_os/modules/skill_creator/__init__.py`

- def `status`
- def `propose_skill`
### class `SkillCreatorModule`
- public: `process`, `propose_evolution`

## `fusion_hero_os/modules/timespace_token/bottleneck.py`

- def `build_competition_qubo`
- def `greedy_bottleneck_assignment`
- def `qubo_energy`

## `fusion_hero_os/modules/timespace_token/geometry.py`

### class `Timescale`
- (Datenklasse / ohne Methoden)
### class `TimespaceCoordinate`
- public: `distance_to`
### class `TimespaceManifold`
- public: `default`, `origin_for_depth`, `geometric_priority`, `neighbor_compression`

## `fusion_hero_os/modules/timespace_token/manager.py`

### class `TimespaceTrack`
- (Datenklasse / ohne Methoden)
### class `AllocationReport`
- public: `to_dict`
### class `TimespaceTokenManager`
- public: `allocate`, `allocate_with_report`, `evolve_from_feedback`
- intern: `__init__`, `_fidelity_boost`

## `fusion_hero_os/modules/timespace_token/module.py`

- def `_track_from_dict`
### class `TimespaceTokenCoreModule`
- public: `process`, `peer_review`
- intern: `__init__`

## `fusion_hero_os/modules/weltraudaimonia.py`

### class `WeltraudaimoniaModule`
- public: `process`
- def `_clamp01`

## `fusion_hero_os/orchestration/agents.py`

### class `Message`
- (Datenklasse / ohne Methoden)
### class `MessageBus`
- public: `subscribe`, `publish`, `update_status`, `latest_status`, `all_status`, `history`
- intern: `__init__`
### class `Task`
- (Datenklasse / ohne Methoden)
### class `TaskQueue`
- public: `put`, `get_nowait`, `depth`, `empty`
- intern: `__init__`
- def `default_executor`
### class `Agent`
- public: `start`, `stop`, `join`, `shutdown`, `spawn_subagent`, `dismiss`, `children`, `assign`
- intern: `__init__`, `_post_heartbeat`, `_run`
### class `Supervisor`
- public: `summarize`, `run_until_drained`, `report`
- intern: `__init__`, `_hire`, `_fire_one_idle`, `_least_loaded`, `_outstanding`, `_run`, `_supervise`
- def `_demo`

## `fusion_hero_os/ports.py`

- def `_env_int`
### class `PortMap`
- public: `dashboard_url_local`, `mesh_ops_url`
- def `get_ports`

## `fusion_hero_os/providers/base.py`

### class `LLMResult`
- public: `to_dict`
### class `BaseLLMProvider`
- public: `is_available`, `generate`, `health`
- intern: `__init__`, `_record`

## `fusion_hero_os/providers/claude_provider.py`

### class `ClaudeProvider`
- public: `is_available`, `generate`
- intern: `__init__`

## `fusion_hero_os/providers/everyapi_provider.py`

### class `EveryAPIProvider`
- public: `is_available`, `generate`
- intern: `__init__`

## `fusion_hero_os/providers/grok_provider.py`

### class `GrokProvider`
- public: `is_available`, `generate`
- intern: `__init__`

## `fusion_hero_os/providers/internal_provider.py`

### class `InternalFallbackProvider`
- public: `is_available`, `generate`
- intern: `__init__`, `_build_heroic_context`

## `fusion_hero_os/registry.py`

### class `ModuleStatus`
- (Datenklasse / ohne Methoden)
### class `ModuleUnavailableError`
- (Datenklasse / ohne Methoden)
### class `ModuleSpec`
- (Datenklasse / ohne Methoden)
### class `Registry`
- public: `load`, `load_all`, `get`, `try_get`, `status_report`
- intern: `__init__`
- def `get_registry`
- def `load_all`
- def `get`
- def `status_report`
- def `_print_status_report`

# Teil II — `03_Code/Dashboard`

## `03_Code/Dashboard/agent_resource_allocator.py`

### class `AgentSlot`
- public: `to_dict`
### class `ResourcePlan`
- public: `to_dict`
- def `_tier_for_mode`
- def `_system_pressure`
- def `build_resource_plan`
- def `get_resource_plan`
- def `pick_agent_pool`

## `03_Code/Dashboard/api_extensions.py`

### class `ProfilePayload`
- (Datenklasse / ohne Methoden)
### class `GatePayload`
- (Datenklasse / ohne Methoden)
### class `ChatPayload`
- (Datenklasse / ohne Methoden)
### class `ValidatePayload`
- (Datenklasse / ohne Methoden)
### class `AgentControlPayload`
- (Datenklasse / ohne Methoden)
### class `AutoLoadPayload`
- (Datenklasse / ohne Methoden)
### class `HeroGuideResolvePayload`
- (Datenklasse / ohne Methoden)
### class `CodeValidatePayload`
- (Datenklasse / ohne Methoden)
- def `_orch`
- def `api_load_all`
- def `api_modules`
- def `api_agent_use`
- def `api_agent_control_status`
- def `api_agent_control_history`
- def `api_agent_control_verify`
- def `api_agent_control_pre_check`
- def `api_mainframe_load`
- def `api_layer4_status`
- def `api_foundation_gate`
- def `api_v12_sync`
- def `api_mod_validate`
- def `api_grok_status`
- def `api_heroic_audit_status`
- def `api_heroic_audit_run`
- def `api_heroic_audit_report`
- def `api_claude_science_status`
- def `api_claude_science_analyze`
- def `api_claude_science_chat`
- def `api_provider_status`
- def `api_provider_select`
- def `api_first_install_status`
- def `api_first_install_run`
- def `api_internal_optimize_parallel`
- def `api_grok_chat`
- def `api_meta_layer_status`
- def `api_meta_layer_windows`
- def `api_meta_layer_attach`
- def `api_windows_substrate_tune`
- def `api_windows_cyber_activate`
- def `api_profile_status`
- def `api_profile_set`
- def `api_resources_plan`
- def `api_resources_workflow`
- def `api_v8_math_status`
- def `api_v8_math_verify`
- def `api_v8_orchestrator_status`
- def `api_v8_orchestrator_bootstrap`
- def `api_v8_orchestrator_query`
- def `api_bridge_ipc_status`
- def `api_bridge_ipc_dispatch`
- def `api_phone_link_status`
- def `api_graph_connectors`
- def `api_graph_connector_status`
- def `api_graph_connector_dispatch`
- def `api_graph_instagram_publish`
- def `api_hero_autoupdate_status`
- def `api_hero_autoupdate_touch`
- def `api_hero_autoupdate_tick`
- def `api_hero_autoupdate_config`
- def `api_phone_link_messages`
- def `api_phone_link_conversations`
- def `api_discovery`
- def `api_connectivity`
- def `api_process_exclusivity_status`
- def `api_settings_sync`
- def `api_settings_schema`
- def `api_settings_get`
- def `api_settings_set`
- def `api_settings_reset`
- def `api_faden_status`
- def `api_faden_threads`
- def `api_faden_upsert`
- def `api_faden_delete`
- def `api_faden_prune`
- def `api_watch_create_room`
- def `api_watch_room_info`
- def `api_watch_room_state`
- def `api_watch_room_cmd`
- def `api_watch_network`
- def `api_watch_realtime_config`
- def `api_watch_room_qr`
- def `api_viz_geisterjagd_banach`
- def `api_suite_status`
- def `api_suite_pipeline_status`
- def `api_suite_pipeline_run`
### class `GhosthuntPayload`
- (Datenklasse / ohne Methoden)
- def `api_suite_ghosthunt`
- def `api_signal_health`
- def `api_jobs_list`
- def `api_job_get`
- def `api_llama_status`
- def `api_llama_chat`
- def `api_llama_qubo_status`
- def `api_llama_subagent_tests_status`
- def `api_llama_subagent_tests_run`
- def `api_agent_backend_policy`
- def `api_agent_backend_dual_run`
- def `api_agent_backend_invoke`
- def `api_subagents_llama_test`
- def `api_context_window_status`
- def `api_context_window_init`
- def `api_context_window_subagent`
- def `api_context_window_feedback`
- def `api_medienserver_status`
- def `api_autoload_status`
- def `api_autoload_run`
- def `api_preload_all`
- def `api_hero_guide_status`
- def `api_hero_guide_audit`
- def `api_hero_guide_resolve`
- def `api_knowledge_graph_status`
- def `api_knowledge_graph_nodes`
- def `api_knowledge_graph_write`
- def `api_mod_validate_code`

## `03_Code/Dashboard/api_plane_routes.py`

- def `_planes`
- def `api_planes_status`
- def `api_planes_classify`
- def `business_root`
- def `business_health`
- def `business_businessplan`
- def `business_pricing`
- def `business_energy`
- def `business_cost_function`
- def `hyperraum_root`
- def `hyperraum_status`
- def `hyperraum_operator`
- def `hyperraum_headset`
- def `hyperraum_headset_set_active`

## `03_Code/Dashboard/app.py`

- def `detect_input_factors`
- def `detect_output_factors`
- def `get_input_factors`
- def `get_output_factors`
### class `AutoLoader`
- public: `register`, `run`, `status`
- intern: `__init__`, `_register_default_drivers`
### class `EventIn`
- (Datenklasse / ohne Methoden)
### class `MetricsOut`
- (Datenklasse / ohne Methoden)
- def `_send_safe`
- def `emit`
- def `heroic_core_event_loop`
- def `_schedule_agent_audit`
- def `_start_supabase_background`
- def `_acquire_dashboard_lock`
- def `startup_event`
- def `shutdown_event`
- def `post_event`
- def `index`
- def `heroic_page`
- def `about_page`
- def `donation_page`
- def `foundation_page`
- def `_load_wallet`
- def `_save_wallet`
- def `api_wallet_get`
### class `WalletUpdate`
- (Datenklasse / ohne Methoden)
- def `api_wallet_update`
- def `watch_create_redirect`
- def `watch_room`
- def `api_gui_status`
- def `api_gui_workspace`
- def `get_metrics`
- def `websocket_endpoint`
- def `watch_party_ws`
- def `api_health`
- def `api_supabase_health`
- def `_ensure_agents`
### class `InputPayload`
- (Datenklasse / ohne Methoden)
### class `OrchestratePayload`
- (Datenklasse / ohne Methoden)
- def `get_hyperthreading`
- def `post_hyperthreading`
- def `api_agents`
- def `api_agents_load`
- def `api_agents_assign`
- def `api_input`
- def `api_orchestrate`
- def `api_input_factors`
- def `api_output_factors`
- def `api_autoload_run`
- def `api_autoload_status`
- def `api_gpu_memory`
- def `api_gpu_allocator_rebalance`
- def `api_gpu_allocator_status`
- def `api_cpu_tuner_status`
- def `api_cpu_tuner_run`
- def `api_resource_coupler_status`
- def `api_resource_coupler_run`
- def `api_gpu_compute_status`
- def `api_gpu_compute_boost`
- def `api_memory_status`
- def `api_memory_relieve`
- def `api_gpu_vram_prioritize`
- def `api_supabase_events`
- def `api_supabase_tables`
- def `api_llama_train`
- def `api_supabase_node_health`
- def `api_supabase_sync_metrics`
- def `api_supabase_sync_status`
- def `api_supabase_audit`
- def `api_supabase_settings_pull`

## `03_Code/Dashboard/architecture_routes.py`

- def `_load_atlas`
- def `api_architecture_atlas`
- def `api_multimodal_inventory`
- def `architecture_page`

## `03_Code/Dashboard/autoloader.py`

### class `DriverSpec`
- public: `to_dict`
### class `ProcessSpec`
- public: `to_dict`
- def `catalog`
- def `_set_driver`
- def `_load_windows_skin`
- def `_tune_windows_substrate`
- def `_load_profile`
- def `_load_hyperthreading`
- def `_warm_worker_pools`
- def `_load_signal_network`
- def `_load_grok`
- def `_load_registry_bundle`
- def `_load_meta_layer`
- def `_probe_windows_drivers_light`
- def `_probe_processes`
- def `run_autoload_sync`
- def `_run_autoload_sync_impl`
- def `run_autoload`
- def `autoload_status`
- def `schedule_deferred_full`

## `03_Code/Dashboard/backends/base.py`

### class `SolverBackend`
- public: `solve`

## `03_Code/Dashboard/backends/classical.py`

### class `EudaimoniaGuard`
- public: `validate_result`
### class `ClassicalBackend`
- public: `solve`
- intern: `__init__`

## `03_Code/Dashboard/boot_optimizer.py`

- def `_medienserver_path`
- def `medienserver_sync_needed`
- def `sync_status`
- def `boot_plan`
- def `optimize_steps`

## `03_Code/Dashboard/business_plan_routes.py`

- def `api_businessplan`
- def `api_businessplan_energy_model`
- def `api_energy_status`
- def `api_energy_tick`
- def `api_subcontractor_pricing`

## `03_Code/Dashboard/connectivity.py`

- def `dashboard_port`
- def `_score_ip`
- def `list_lan_ips`
- def `best_lan_ip`
- def `local_network_base`
- def `_device_id`
- def `build_discovery`
- def `build_connectivity_summary`

## `03_Code/Dashboard/connectors_routes.py`

### class `CallRequest`
- (Datenklasse / ohne Methoden)
- def `list_connectors`
- def `connector_detail`
- def `connector_health`
- def `connector_call`

## `03_Code/Dashboard/control_instances_routes.py`

### class `ControlIn`
- (Datenklasse / ohne Methoden)
- def `control_status`
- def `control_run`

## `03_Code/Dashboard/cyber_layer_windows.py`

### class `CyberSignal`
- public: `to_dict`
### class `CyberLayerState`
- public: `to_dict`
- def `_read_file`
- def `_write_file`
- def `_build_signals`
- def `_score`
- def `activate_cyber_layer`
- def `pulse_cyber_layer`
- def `get_cyber_layer_status`

## `03_Code/Dashboard/domain/entities.py`

### class `QUBOProblem`
- intern: `__init__`
### class `SolverResult`
- intern: `__init__`
### class `QUBOSolverConfig`
- intern: `__init__`

## `03_Code/Dashboard/dual_timeline_routes.py`

- def `dt_status`
- def `dt_run`
- def `dt_catalog`

## `03_Code/Dashboard/faden_store.py`

- def `_state_root`
- def `_index_path`
### class `FadenThread`
- public: `to_dict`, `from_dict`
- def `strength_from_lambda`
- def `_expires_for_strength`
### class `FadenStore`
- public: `prune`, `upsert`, `get`, `list_threads`, `delete`, `status`
- intern: `__init__`, `_load`, `_save`, `_upsert_locked`
- def `get_faden_store`

## `03_Code/Dashboard/fusion_profile.py`

### class `FusionProfileState`
- public: `to_dict`
- def `_read_file`
- def `_write_file`
- def `get_active_profile_name`
- def `get_profile_config`
- def `set_profile`
- def `profile_status`
- def `apply_performance_level`

## `03_Code/Dashboard/fusion_settings.py`

- def `_bool_str`
- def `_read_file`
- def `_write_file`
- def `_core_module_options`
- def `_resolve_options`
- def `_current_value`
- def `get_schema`
- def `get_values`
- def `_as_bool`
- def `_apply_side_effects`
- def `apply_settings`
- def `boot_load`
- def `reset_defaults`

## `03_Code/Dashboard/grok_bridge.py`

### class `GrokMessage`
- public: `to_dict`
### class `GrokChatResult`
- public: `to_dict`
### class `GrokBridge`
- public: `chat`, `status`
- intern: `__init__`, `_load_skill_excerpt`, `_detect_intents`, `_build_context_block`
- def `get_grok_bridge`

## `03_Code/Dashboard/grok_interconnect_routes.py`

- def `_capture_evolve`
- def `api_grok_interconnect`
- def `api_grok_interconnect_capture`
- def `api_grok_route`
- def `api_grok_routes_table`
- def `redir_grok`
- def `redir_grok_status`
- def `redir_grok_chat`
- def `redir_interconnect`
- def `redir_ide`
- def `redir_worktree`
- def `redir_portal`
- def `redir_mainframe_website`
- def `redir_vr_persistent`
- def `redir_api_interconnect`
- def `api_route_redirect`
- def `mainframe_grok_page`

## `03_Code/Dashboard/gui/era_design.py`

- def `_skin_css_block`
- def `workspace_css`
- def `cyber_layer_css`
- def `monitor_css`
- def `era_meta`

## `03_Code/Dashboard/gui/fusion_gui.py`

- def `get_gui_status`
- def `workspace_script_path`

## `03_Code/Dashboard/gui/input_bridge.py`

- def `api_call`
- def `call_api`
- def `submit_input`
- def `fetch_signal_pulse`
- def `fetch_health_full`
- def `fetch_jobs`

## `03_Code/Dashboard/gui/interactions.py`

- def `inject_drag_script`
- def `register_draggable`
- def `init_panel_drag`
- def `safe_run_javascript`
- def `inject_drag_boot`
- def `reset_panel_positions`
- def `set_action_refs`
- def `is_busy`
- def `async_action`
- def `copy_to_clipboard`
- def `bind_enter`
- def `job_status_class`
- def `format_job_row`

## `03_Code/Dashboard/gui/layer_panels.py`

- def `build_stack_layers`
- def `_layer_panel`

## `03_Code/Dashboard/gui/task_panels.py`

- def `build_task_layer`
- def `_panel_jobs`
- def `_panel_quick`
- def `_panel_hints`
- def `render_job_list`

## `03_Code/Dashboard/gui/theme_3d.py`

- def `inject_theme`
- def `metric_bar_html`
- def `update_metric_bar`

## `03_Code/Dashboard/gui/web_scripts.py`

- def `drag_script`

## `03_Code/Dashboard/heroic_core_gui(2).py`

### class `AdaptiveLimitWarning`
- public: `update`
- intern: `__init__`
- def `boegen_self_synthesis`
### class `HeroicCoreGUI`
- public: `calculate_limit`, `run_boegen_synthesis`, `send_to_grok`, `apply_grok_response`
- intern: `__init__`, `_setup_style`, `_create_widgets`, `_build_limit_tab`, `_build_boegen_tab`, `_build_grok_tab`, `_build_info_tab`

## `03_Code/Dashboard/heroic_core_gui.py`

### class `AdaptiveLimitWarning`
- public: `update`
- intern: `__init__`
- def `boegen_self_synthesis`
### class `HeroicCoreGUI`
- public: `calculate_limit`, `run_boegen_synthesis`
- intern: `__init__`, `_setup_style`, `_create_widgets`, `_build_limit_tab`, `_build_boegen_tab`, `_build_info_tab`

## `03_Code/Dashboard/heroic_core_mainframe.py`

- def `parallel_worker_count`
### class `SelfModifyCoreModule`
- public: `register_audit_hook`
- intern: `__init__`
### class `GenerationalEvolutionProtocolCoreModule`
- public: `run_generation`
- intern: `__init__`
### class `CriticalMetaAnalysisCoreModule`
- public: `analyze`
### class `ExecutableAuditAgent`
- intern: `__init__`
### class `QUBOIntegrationCoreModule`
- public: `execute_secure_run`, `execute_parallel_run`
- intern: `__init__`, `_interlock_core_hooks`

## `03_Code/Dashboard/input_gateway.py`

### class `InputAck`
- public: `to_dict`
- def `_new_job_id`
- def `validate_input`
- def `classify_message`
- def `accept_input`
- def `build_job_payload`

## `03_Code/Dashboard/layered_signal_network.py`

### class `SignalEnvelope`
- public: `to_dict`
### class `_SignalSession`
- intern: `__init__`
- def `_session_id`
- def `_get_session`
- def `_hash_payload`
- def `_estimate_bytes`
- def `_flatten_delta`
- def `_pulse_payload`
- def `_batch_payload`
- def `emit_signal`
- def `network_stats`

## `03_Code/Dashboard/mainframe_background.py`

- def `cost_analysis_loop`
- def `repo_mirror_loop`
- def `energy_pricing_loop`
- def `hero_autoupdate_loop`
- def `start_mainframe_daemons`

## `03_Code/Dashboard/mainframe_ops_routes.py`

- def `api_cost_status`
- def `api_cost_tick`
- def `api_repo_status`
- def `api_repo_tick`
- def `api_ops_summary`
- def `mainframe_ops_page`

## `03_Code/Dashboard/mainframe_site_routes.py`

- def `_repo`
- def `_safe_join`
- def `_tpl`
- def `_git_worktrees`
- def `_related_trees`
- def `_list_dir`
- def `mainframe_hub`
- def `mainframe_vr_persistent`
- def `mainframe_ide`
- def `mainframe_worktree_page`
- def `mainframe_worktree_view`
- def `api_site_status`
- def `api_worktree_list`
- def `api_worktree_git`
- def `api_worktree_file_meta`
- def `api_worktree_raw`
- def `api_worktree_content`
- def `api_ide_status`

## `03_Code/Dashboard/mesh_ops_routes.py`

- def `_ts_exe`
- def `_tailscale_status`
- def `_funnel_status`
- def `_poly_mesh`
- def `_entwicklungsquant_status`
- def `_registry_stubs_cleared`
- def `_quantize_selfmod_status`
- def `mesh_ops_root`
- def `mesh_ops_tailscale`
- def `mesh_ops_funnel`
- def `mesh_ops_poly`
- def `mesh_ops_quant`
- def `mesh_ops_quantize_selfmod`
- def `mesh_ops_quantize_selfmod_ensure`
- def `mesh_ops_quantize_selfmod_modulate`
- def `mesh_ops_quantize_selfmod_cycle`
- def `mesh_ops_p1`
- def `mesh_ops_mainframe_laden`
- def `mesh_ops_once_mint`
- def `mesh_ops_dns_encrypt`
- def `mesh_ops_identity`
- def `mesh_ops_schwerkraft`
- def `mesh_ops_mtc_status`
- def `mesh_ops_mtc_roll`
- def `mesh_once_redeem`

## `03_Code/Dashboard/meta_layer_windows.py`

### class `WindowsSubstrate`
- public: `to_dict`
### class `MetaLayerProcess`
- public: `to_dict`
### class `MetaLayerState`
- public: `to_dict`
- def `set_internal_backend_context`
- def `_read_state_file`
- def `_write_state_file`
- def `scan_windows_substrate`
- def `scan_fusion_processes`
- def `probe_stack_health`
- def `attach_meta_layer`
- def `get_meta_layer_status`
- def `heartbeat_meta_layer`

## `03_Code/Dashboard/module_registry.py`

### class `AgentInfo`
- public: `to_dict`
### class `ModuleInfo`
- public: `to_dict`
### class `FusionRegistry`
- public: `load_all`, `set_hyperthreading`, `list_modules`, `list_agents`, `resource_plan`, `use_agent`, `layer4_status`, `mainframe_pipeline_status`
- intern: `__init__`, `_catalog`, `_scan_agents`, `_sync_medienserver`
- def `get_registry`

## `03_Code/Dashboard/process_worker.py`

### class `JobRecord`
- public: `to_dict`
- def `_get_proc_pool`
- def `_get_io_pool`
- def `warm_pools`
- def `pool_status`
- def `_trim_jobs`
- def `register_job`
- def `get_job`
- def `list_jobs`
- def `_run_in_subprocess`
- def `_run_in_thread`
- def `_apply_worker_side_effects`
- def `_is_heavy`
- def `submit_job`
- def `submit_job_async`

## `03_Code/Dashboard/pseudo_inhouse_creative_routes.py`

### class `CreateIn`
- (Datenklasse / ohne Methoden)
### class `OpenAIImageRequest`
- (Datenklasse / ohne Methoden)
- def `creative_status`
- def `creative_catalog`
- def `creative_artifacts`
- def `creative_create`
- def `creative_image`
- def `creative_pdf`
- def `creative_video`
- def `creative_graphics`
- def `creative_file`
- def `openai_images`

## `03_Code/Dashboard/pseudo_inhouse_routes.py`

### class `ChatIn`
- (Datenklasse / ohne Methoden)
### class `OpenAIMessage`
- (Datenklasse / ohne Methoden)
### class `OpenAIChatRequest`
- (Datenklasse / ohne Methoden)
- def `_hub`
- def `api_inhouse_status`
- def `api_inhouse_catalog`
- def `api_inhouse_chat`
- def `openai_list_models`
- def `openai_chat_completions`
- def `api_inhouse_health`

## `03_Code/Dashboard/scripts/build_geisteskrankheiten_4d_kompendium.py`

- def `_read`
- def `_v7_body`
- def `_merge`
- def `main`

## `03_Code/Dashboard/scripts/build_geisteskrankheiten_4d_v4.py`

- def `_read`
- def `_merge`
- def `_write_pdf`
- def `_write_index`
- def `main`

## `03_Code/Dashboard/scripts/build_geisteskrankheiten_4d_v5.py`

- def `_read`
- def `_v4_source`
- def `_merge`
- def `_write_pdf`
- def `_write_index`
- def `main`

## `03_Code/Dashboard/scripts/build_geisteskrankheiten_4d_v6.py`

- def `_read`
- def `_v5_source`
- def `_merge`
- def `_write_pdf`
- def `main`

## `03_Code/Dashboard/scripts/build_geisteskrankheiten_4d_v7.py`

- def `_read`
- def `_v6`
- def `_merge`
- def `_write_pdf`
- def `main`

## `03_Code/Dashboard/scripts/improve_geisteskrankheiten_4d.py`

- def `_load_source`
- def `_run_claude_science`
- def `_run_local_llama`
- def `_build_improved_markdown`
- def `_write_pdf`
- def `main`

## `03_Code/Dashboard/scripts/kompendium_pdf_renderer.py`

- def `_styles`
- def `_chapter_label`
- def `_clean_inline`
- def `_part_for_section`
### class `_KompendiumCanvas`
- intern: `__init__`, `__call__`
- def `_parse_table`
### class `_SVGFigure`
- public: `wrap`, `draw`
- intern: `__init__`
- def `_insert_figures`
- def `_collect_headings`
- def `render_kompendium_pdf`

## `03_Code/Dashboard/scripts/mer_diagram_generator.py`

- def `_svg_header`
- def `_svg_footer`
- def `_save`
- def `diagram_4d_overview`
- def `_axis_plane`
- def `diagram_pi_kg`
- def `diagram_pi_sn`
- def `diagram_schattenhuelle`
- def `diagram_bipolar_cycle`
- def `diagram_ptbs_attraktor`
- def `diagram_alpha_phases`
- def `diagram_schichten_pipeline`
- def `diagram_memetisch_mimetisch`
- def `generate_all`

## `03_Code/Dashboard/scripts/run_heroic_science_audit.py`

- def `main`

## `03_Code/Dashboard/supabase_background.py`

- def `_sync_enabled`
- def `metrics_loop`
- def `phone_link_snapshot_loop`
- def `watch_server_sync_loop`
- def `start_background_tasks`

## `03_Code/Dashboard/supabase_client.py`

- def `_env`
- def `is_configured`
- def `get_client`
- def `probe`
- def `status`

## `03_Code/Dashboard/supabase_store.py`

- def `_ensure_ready`
- def `refresh_ready`
- def `cloud_sync_enabled`
- def `device_id`
- def `_insert`
- def `_upsert`
- def `save_event`
- def `save_metrics`
- def `save_job`
- def `save_llama_config`
- def `list_recent_events`
- def `save_watch_room`
- def `load_watch_room`
- def `load_watch_rooms`
- def `save_settings_cloud`
- def `load_settings_cloud`
- def `pull_settings_from_cloud`
- def `save_agent_audit`
- def `save_phone_link_snapshot`
- def `save_faden_thread`
- def `load_faden_threads`
- def `save_fractal_manifest`
- def `load_latest_fractal_manifest`
- def `save_mesh_exit_state`
- def `list_recent_agent_audit`
- def `store_status`
- def `check_tables`
- def `sync_status`
- def `roundtrip_test`

## `03_Code/Dashboard/vr_routes.py`

- def `_scan_scene_files`
- def `_hl_path`
- def `_ensure_hl_import`
- def `highest_layer_page`
- def `highest_layer_vr_page`
- def `vr_persistent_redirect`
- def `vr_viewer`
- def `vr_asset_file`
- def `api_vr_assets`
- def `api_vr_roadmap`
- def `api_vr_status`

## `03_Code/Dashboard/watch_party.py`

### class `WatchRoom`
- public: `current_position`, `bump_revision`, `to_state`
### class `WatchPartyManager`
- public: `hydrate_from_cloud`, `extract_video_id`, `create_room`, `get_room`, `ensure_room`, `register_ws`, `unregister_ws`, `subscribers`, `apply_command`, `room_info`
- intern: `__init__`, `_room_row`, `_persist_room`, `_finalize_command`, `_ensure_controller`, `_apply_command_locked`
- def `_server_sync_flag`
- def `get_watch_manager`
- def `local_network_base`
- def `join_url_for_room`
- def `render_watch_page`
- def `broadcast_room_state`

## `03_Code/Dashboard/watch_realtime_server.py`

- def `watch_realtime_listener`
- def `start_watch_realtime_task`

## `03_Code/Dashboard/watch_sync_server.py`

- def `server_sync_enabled`
- def `realtime_enabled`
- def `server_poll_interval_sec`
- def `active_poll_interval_sec`
- def `poll_fallback_only`
- def `get_realtime_client_config`
- def `extract_realtime_row`
- def `row_to_watch_state`
- def `apply_realtime_payload`
- def `merge_row_into_room`
- def `refresh_room_from_server`
- def `_refresh_room_from_server_locked`
- def `push_room_to_server`
- def `_push_room_to_server_locked`
- def `low_latency_enabled`
- def `finalize_command`
- def `state_response`
- def `get_authoritative_state`
- def `active_room_ids`

## `03_Code/Dashboard/windows_perf_tuner.py`

### class `TuneAction`
- public: `to_dict`
- def `_run_ps`
- def `_list_power_schemes`
- def `_active_power_scheme`
- def `_resolve_high_performance_guid`
- def `_fusion_backend_pids`
- def `scan_windows_perf`
- def `_recommendations`
- def `_resolve_balanced_guid`
- def `_set_power_balanced`
- def `apply_windows_performance_level`
- def `_set_power_high`
- def `_dedupe_backends`
- def `_boost_own_priority`
- def `_set_substrate_env`
- def `apply_substrate_tuning`
- def `apply_windows_tuning`
- def `substrate_status`
- def `_cyber_layer_brief`
- def `tuner_status`

## `03_Code/Dashboard/windows_skin.py`

### class `WindowsSkin`
- public: `to_dict`
- def `_read_json`
- def `_write_json`
- def `list_presets`
- def `_load_preset`
- def `_merge_skin`
- def `_merge_dict`
- def `load_skin`
- def `set_preset`
- def `patch_user_skin`
- def `reset_user_skin`
- def `skin_css_variables`
- def `skin_layer_css`
- def `render_full_skin_css`
- def `skin_status`
- def `ensure_user_skin_template`

## `03_Code/Dashboard/worker_runner.py`

- def `main`

## `03_Code/Dashboard/worker_tasks.py`

- def `_load_all`
- def `_solve_qubo`
- def `_health_light`
- def `execute_intent`
- def `execute_job`

## `03_Code/Dashboard/workspace.py`

- def `trigger_core_mod`
- def `check_and_assign_task`
- def `complete_task`
- def `toggle_autonomous`
- def `auto_generate_and_assign`
- def `run_auto_save`
- def `end_session_and_push`
- def `toggle_auto_git_save`
- def `periodic_git_save`
- def `build_workspace`

## `03_Code/Dashboard/x402_routes.py`

### class `X402RunIn`
- (Datenklasse / ohne Methoden)
- def `x402_status`
- def `x402_run`

